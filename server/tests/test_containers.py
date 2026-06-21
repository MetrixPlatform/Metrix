import time

from test_auth_rbac import create_client, install_sqlite, login

from app.core.permissions import ADMIN_ROLE
from app.modules.containers import CONTAINER_MANAGE_OTHERS

CONTAINER_CODES = {
    "action:container:create",
    "action:container:read",
    "action:container:update",
    "action:container:delete",
    "action:container:operate",
}


class FakeImage:
    def __init__(self, image_id: str, tags: list[str]):
        self.id = image_id
        self.short_id = image_id.replace("sha256:", "")[:12]
        self.tags = tags
        self.attrs = {"Id": image_id, "RepoTags": tags, "Size": 1024, "Created": "2026-06-15T00:00:00Z", "Config": {"Labels": {}}}

    def save(self, named=True):
        yield b"fake-image-tar"


class FakeContainer:
    def __init__(self, container_id: str, name: str, image: str, owner: int | None):
        self.id = container_id
        self.short_id = container_id[:12]
        self.name = name
        self.status = "created"
        labels = {}
        if owner is not None:
            labels = {"metrix.created_by": "metrix", "metrix.owner_user_id": str(owner), "metrix.resource_type": "container"}
        self.attrs = {
            "Id": container_id,
            "Created": "2026-06-15T00:00:00Z",
            "Config": {"Image": image, "Labels": labels},
            "State": {"Status": self.status},
            "NetworkSettings": {"Ports": {}},
            "Mounts": [],
        }
        self.started = False
        self.removed = False

    def start(self):
        self.started = True
        self.status = "running"
        self.attrs["State"]["Status"] = "running"

    def stop(self):
        self.status = "exited"
        self.attrs["State"]["Status"] = "exited"

    def restart(self):
        self.started = True
        self.status = "running"
        self.attrs["State"]["Status"] = "running"

    def remove(self, force=False):
        self.removed = True

    def logs(self, tail=200, timestamps=True):
        return b"2026-06-15T00:00:00Z hello\n"


class FakeContainerCollection:
    def __init__(self, engine):
        self.engine = engine

    def list(self, all=True):
        return list(self.engine.containers_by_id.values())

    def get(self, container_id):
        return self.engine.containers_by_id[container_id]

    def create(self, **kwargs):
        owner = int(kwargs["labels"]["metrix.owner_user_id"])
        container_id = f"container-{len(self.engine.containers_by_id) + 1}"
        container = FakeContainer(container_id, kwargs["name"], kwargs["image"], owner)
        container.attrs["Mounts"] = [
            {"Type": "volume", "Name": name, "Destination": config["bind"]}
            for name, config in (kwargs.get("volumes") or {}).items()
        ]
        self.engine.containers_by_id[container_id] = container
        self.engine.last_create = kwargs
        return container


class FakeImageCollection:
    def __init__(self, engine):
        self.engine = engine

    def list(self):
        return list(self.engine.images_by_id.values())

    def get(self, image_ref):
        for image in self.engine.images_by_id.values():
            if image.id == image_ref or image_ref in image.tags:
                return image
        raise KeyError(image_ref)

    def remove(self, image_ref, force=False, noprune=False):
        image = self.get(image_ref)
        self.engine.removed_images.append(image.id)
        self.engine.images_by_id.pop(image.id, None)

    def load(self, data):
        image = FakeImage("sha256:imported", ["imported:latest"])
        self.engine.images_by_id[image.id] = image
        return [image]


class FakeVolumeCollection:
    def __init__(self):
        self.volumes_by_name = {}

    def get(self, name):
        if name not in self.volumes_by_name:
            raise KeyError(name)
        return self.volumes_by_name[name]

    def list(self):
        return list(self.volumes_by_name.values())

    def create(self, name, driver="local", labels=None):
        volume = FakeVolume(name, driver, labels or {}, self)
        self.volumes_by_name[name] = volume
        return volume


class FakeVolume:
    def __init__(self, name: str, driver: str, labels: dict, collection: FakeVolumeCollection):
        self.name = name
        self.collection = collection
        self.removed = False
        self.attrs = {
            "Name": name,
            "Driver": driver,
            "Scope": "local",
            "Mountpoint": f"/var/lib/docker/volumes/{name}/_data",
            "Labels": labels,
            "Options": {},
            "CreatedAt": "2026-06-15T00:00:00Z",
        }

    def remove(self, force=False):
        self.removed = True
        self.collection.volumes_by_name.pop(self.name, None)


class FakeDockerEngine:
    def __init__(self):
        self.images_by_id = {"sha256:base": FakeImage("sha256:base", ["python:3.12"])}
        self.containers_by_id = {
            "own-container": FakeContainer("own-container", "metrix-u2-job", "python:3.12", 2),
            "other-container": FakeContainer("other-container", "metrix-u3-job", "python:3.12", 3),
        }
        self.removed_images = []
        self.last_create = {}
        self.containers = FakeContainerCollection(self)
        self.images = FakeImageCollection(self)
        self.volumes = FakeVolumeCollection()

    def ping(self):
        return True

    def info(self):
        return {"OSType": "linux", "Architecture": "x86_64", "Containers": len(self.containers_by_id), "Images": len(self.images_by_id)}

    def version(self):
        return {"Version": "26.0.0"}


def install_fake_docker(monkeypatch, engine: FakeDockerEngine):
    from app.modules.containers.clients import DockerAdapter

    monkeypatch.setattr("app.modules.containers.clients.create_client", lambda config=None: DockerAdapter(engine, "fake://docker"))


def grant_container_role(client, admin_headers, code):
    permissions = client.get("/api/permissions", headers=admin_headers).json()
    permission_ids_by_code = {item["code"]: item["id"] for item in permissions}
    role = client.post("/api/roles", json={"code": code, "name": code, "description": ""}, headers=admin_headers)
    assert role.status_code == 200
    role_id = role.json()["id"]
    assign = client.put(
        f"/api/roles/{role_id}/permissions",
        json={"permission_ids": [permission_ids_by_code[item] for item in CONTAINER_CODES]},
        headers=admin_headers,
    )
    assert assign.status_code == 200
    return role_id


def create_container_user(client, admin_headers, username, role_id, phone):
    response = client.post(
        "/api/users",
        json={
            "username": username,
            "password": "Container123",
            "full_name": username,
            "phone": phone,
            "email": f"{username}@example.com",
            "company": "",
            "department": "",
            "role_ids": [role_id],
        },
        headers=admin_headers,
    )
    assert response.status_code == 200
    return login(client, username, "Container123"), response.json()["id"]


def test_admin_login_permissions_include_container_permissions_when_role_binding_is_stale(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)

    from app.db.session import get_session_factory
    from app.models import Permission, Role

    with get_session_factory()() as db:
        admin_role = db.query(Role).filter(Role.code == ADMIN_ROLE).one()
        permission = db.query(Permission).filter(Permission.code == CONTAINER_MANAGE_OTHERS).one()
        admin_role.permissions.remove(permission)
        db.commit()

    response = client.post("/api/auth/login", json={"username": payload["admin_username"], "password": payload["admin_password"]})
    assert response.status_code == 200
    assert CONTAINER_MANAGE_OTHERS in response.json()["permissions"]


def test_container_permissions_and_owner_isolation(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    engine = FakeDockerEngine()
    install_fake_docker(monkeypatch, engine)
    role_id = grant_container_role(client, admin_headers, "container_user")
    user_headers, user_id = create_container_user(client, admin_headers, "container_user", role_id, "13800000041")

    engine.containers_by_id["own-container"].attrs["Config"]["Labels"]["metrix.owner_user_id"] = str(user_id)
    engine.containers_by_id["other-container"].attrs["Config"]["Labels"]["metrix.owner_user_id"] = str(user_id + 1)

    status = client.get("/api/container-engine/status", headers=user_headers)
    assert status.status_code == 200
    assert status.json()["available"] is True
    assert status.json()["docker_host"] == "fake://docker"

    visible = client.get("/api/container-instances", headers=user_headers)
    assert visible.status_code == 200
    assert [item["id"] for item in visible.json()["items"]] == ["own-container"]

    denied_logs = client.get("/api/container-instances/other-container/logs", headers=user_headers)
    assert denied_logs.status_code == 403


def test_container_image_records_and_create_container(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    engine = FakeDockerEngine()
    install_fake_docker(monkeypatch, engine)
    role_id = grant_container_role(client, admin_headers, "container_creator")
    user_headers, user_id = create_container_user(client, admin_headers, "container_creator", role_id, "13800000042")

    visible_default = client.get("/api/container-images", headers=user_headers)
    assert visible_default.status_code == 200
    assert visible_default.json()["total"] == 1
    assert visible_default.json()["items"][0]["is_public"] is True
    assert visible_default.json()["items"][0]["owner_user_id"] is None

    denied_delete = client.delete("/api/container-images/python%3A3.12", headers=user_headers)
    assert denied_delete.status_code == 403

    public = client.put("/api/container-images/python%3A3.12/visibility", json={"is_public": True}, headers=admin_headers)
    assert public.status_code == 200

    visible = client.get("/api/container-images", headers=user_headers)
    assert visible.status_code == 200
    assert visible.json()["total"] == 1

    created = client.post(
        "/api/container-instances",
        json={
            "name": "job",
            "image": "python:3.12",
            "command": "python main.py",
            "env": {"NORMAL": "1", "PASSWORD": "hidden"},
            "ports": [{"container_port": "8080", "host_port": 18080, "protocol": "tcp"}],
            "volumes": [{"container_path": "/data", "volume_name": "job_data", "read_only": False}],
            "restart_policy": "no",
            "memory_limit_mb": 128,
            "cpu_limit": 1,
            "auto_start": True,
        },
        headers=user_headers,
    )
    assert created.status_code == 200
    body = created.json()
    assert body["owner_user_id"] == user_id
    assert body["name"] == f"metrix-u{user_id}-job"
    assert engine.last_create["labels"]["metrix.owner_user_id"] == str(user_id)
    assert "PASSWORD" not in engine.last_create["environment"]
    assert engine.volumes.volumes_by_name["job_data"].attrs["Labels"]["metrix.owner_user_id"] == str(user_id)


def test_private_container_image_is_hidden_from_other_users(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    engine = FakeDockerEngine()
    install_fake_docker(monkeypatch, engine)
    owner_role_id = grant_container_role(client, admin_headers, "container_image_owner")
    other_role_id = grant_container_role(client, admin_headers, "container_image_other")
    owner_headers, _owner_id = create_container_user(client, admin_headers, "container_image_owner", owner_role_id, "13800000044")
    other_headers, _other_id = create_container_user(client, admin_headers, "container_image_other", other_role_id, "13800000045")

    imported = client.post(
        "/api/container-images/import",
        files={"file": ("image.tar", b"fake", "application/octet-stream")},
        headers=owner_headers,
    )
    assert imported.status_code == 200
    _wait_job_success(client, owner_headers, imported.json()["job_id"])

    owner_images = client.get("/api/container-images?keyword=imported", headers=owner_headers)
    assert owner_images.status_code == 200
    assert owner_images.json()["total"] == 1
    assert owner_images.json()["items"][0]["is_public"] is False

    other_images = client.get("/api/container-images?keyword=imported", headers=other_headers)
    assert other_images.status_code == 200
    assert other_images.json()["total"] == 0

    denied_create = client.post(
        "/api/container-instances",
        json={
            "name": "private-image",
            "image": "imported:latest",
            "command": "sh",
            "env": {},
            "ports": [],
            "volumes": [],
            "restart_policy": "no",
            "memory_limit_mb": None,
            "cpu_limit": None,
            "auto_start": False,
        },
        headers=other_headers,
    )
    assert denied_create.status_code == 403
    assert client.post("/api/container-images/imported%3Alatest/export", headers=other_headers).status_code == 403


def test_deleting_private_image_record_keeps_shared_docker_image(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    engine = FakeDockerEngine()
    install_fake_docker(monkeypatch, engine)
    owner_role_id = grant_container_role(client, admin_headers, "container_image_delete_owner")
    other_role_id = grant_container_role(client, admin_headers, "container_image_delete_other")
    owner_headers, _owner_id = create_container_user(client, admin_headers, "container_image_delete_owner", owner_role_id, "13800000046")
    other_headers, other_id = create_container_user(client, admin_headers, "container_image_delete_other", other_role_id, "13800000047")

    imported = client.post(
        "/api/container-images/import",
        files={"file": ("image.tar", b"fake", "application/octet-stream")},
        headers=owner_headers,
    )
    assert imported.status_code == 200
    _wait_job_success(client, owner_headers, imported.json()["job_id"])

    from app.db.session import get_session_factory
    from app.modules.containers.models import ContainerImageRecord

    with get_session_factory()() as db:
        db.add(ContainerImageRecord(image_id="sha256:imported", repo_tags='["imported:latest"]', created_by=other_id))
        db.commit()

    deleted = client.delete("/api/container-images/imported%3Alatest", headers=owner_headers)
    assert deleted.status_code == 200
    assert "sha256:imported" not in engine.removed_images

    other_images = client.get("/api/container-images?keyword=imported", headers=other_headers)
    assert other_images.status_code == 200
    assert other_images.json()["total"] == 1


def test_container_volume_management_and_owner_isolation(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    engine = FakeDockerEngine()
    install_fake_docker(monkeypatch, engine)
    role_id = grant_container_role(client, admin_headers, "container_volume_user")
    user_headers, user_id = create_container_user(client, admin_headers, "container_volume_user", role_id, "13800000043")

    engine.volumes.create(
        "foreign_volume",
        labels={"metrix.created_by": "metrix", "metrix.owner_user_id": str(user_id + 1), "metrix.resource_type": "volume"},
    )
    engine.volumes.create("external_volume", labels={})
    engine.volumes.create(
        "used_volume",
        labels={"metrix.created_by": "metrix", "metrix.owner_user_id": str(user_id), "metrix.resource_type": "volume"},
    )
    engine.containers_by_id["own-container"].attrs["Config"]["Labels"]["metrix.owner_user_id"] = str(user_id)
    engine.containers_by_id["own-container"].attrs["Mounts"] = [{"Type": "volume", "Name": "used_volume"}]

    visible = client.get("/api/container-volumes", headers=user_headers)
    assert visible.status_code == 200
    assert [item["name"] for item in visible.json()["items"]] == ["used_volume"]
    assert visible.json()["items"][0]["used_by"] == ["metrix-u2-job"]

    created = client.post("/api/container-volumes", json={"name": "user_volume", "driver": "local"}, headers=user_headers)
    assert created.status_code == 200
    assert created.json()["owner_user_id"] == user_id
    assert engine.volumes.volumes_by_name["user_volume"].attrs["Labels"]["metrix.owner_user_id"] == str(user_id)

    denied = client.delete("/api/container-volumes/foreign_volume", headers=user_headers)
    assert denied.status_code == 403

    in_use = client.delete("/api/container-volumes/used_volume", headers=user_headers)
    assert in_use.status_code == 400

    deleted = client.delete("/api/container-volumes/user_volume", headers=user_headers)
    assert deleted.status_code == 200
    assert "user_volume" not in engine.volumes.volumes_by_name

    prune_target = client.post("/api/container-volumes", json={"name": "prune_me", "driver": "local"}, headers=user_headers)
    assert prune_target.status_code == 200
    pruned = client.post("/api/container-volumes/prune", headers=user_headers)
    assert pruned.status_code == 200
    assert pruned.json()["deleted"] == ["prune_me"]
    assert "used_volume" in engine.volumes.volumes_by_name
    assert "foreign_volume" in engine.volumes.volumes_by_name
    assert "external_volume" in engine.volumes.volumes_by_name

    admin_visible = client.get("/api/container-volumes?keyword=volume", headers=admin_headers)
    assert admin_visible.status_code == 200
    assert admin_visible.json()["total"] == 3


def test_container_image_import_and_export_jobs(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    engine = FakeDockerEngine()
    install_fake_docker(monkeypatch, engine)

    imported = client.post(
        "/api/container-images/import",
        files={"file": ("image.tar", b"fake", "application/octet-stream")},
        headers=admin_headers,
    )
    assert imported.status_code == 200
    import_job_id = imported.json()["job_id"]
    _wait_job_success(client, admin_headers, import_job_id)

    images = client.get("/api/container-images?keyword=imported", headers=admin_headers)
    assert images.status_code == 200
    assert images.json()["total"] == 1

    exported = client.post("/api/container-images/imported%3Alatest/export", headers=admin_headers)
    assert exported.status_code == 200
    export_job_id = exported.json()["job_id"]
    _wait_job_success(client, admin_headers, export_job_id)

    download = client.get(f"/api/container-jobs/{export_job_id}/download", headers=admin_headers)
    assert download.status_code == 200
    assert download.content == b"fake-image-tar"


def _wait_job_success(client, headers, job_id):
    for _ in range(30):
        jobs = client.get("/api/container-jobs", headers=headers)
        item = next(item for item in jobs.json()["items"] if item["job_id"] == job_id)
        if item["status"] == "success":
            return
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} did not finish")
