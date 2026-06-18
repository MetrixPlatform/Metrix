import type { Component } from "vue";

// Offline file/folder type icons (vscode-icons set, bundled at build time via
// unplugin-icons). Only the icons imported here end up in the bundle. Unknown
// extensions/folders fall back to the default file/folder icons.
import IconDefaultFile from "~icons/vscode-icons/default-file";
import IconDefaultFolder from "~icons/vscode-icons/default-folder";
import IconDefaultFolderOpened from "~icons/vscode-icons/default-folder-opened";

import IconPython from "~icons/vscode-icons/file-type-python";
import IconGo from "~icons/vscode-icons/file-type-go";
import IconCpp from "~icons/vscode-icons/file-type-cpp";
import IconC from "~icons/vscode-icons/file-type-c";
import IconCHeader from "~icons/vscode-icons/file-type-cheader";
import IconCppHeader from "~icons/vscode-icons/file-type-cppheader";
import IconJs from "~icons/vscode-icons/file-type-js";
import IconTs from "~icons/vscode-icons/file-type-typescript";
import IconReactTs from "~icons/vscode-icons/file-type-reactts";
import IconReactJs from "~icons/vscode-icons/file-type-reactjs";
import IconVue from "~icons/vscode-icons/file-type-vue";
import IconJson from "~icons/vscode-icons/file-type-json";
import IconYaml from "~icons/vscode-icons/file-type-yaml";
import IconXml from "~icons/vscode-icons/file-type-xml";
import IconIni from "~icons/vscode-icons/file-type-ini";
import IconToml from "~icons/vscode-icons/file-type-toml";
import IconMarkdown from "~icons/vscode-icons/file-type-markdown";
import IconShell from "~icons/vscode-icons/file-type-shell";
import IconHtml from "~icons/vscode-icons/file-type-html";
import IconCss from "~icons/vscode-icons/file-type-css";
import IconScss from "~icons/vscode-icons/file-type-scss";
import IconLess from "~icons/vscode-icons/file-type-less";
import IconSql from "~icons/vscode-icons/file-type-sql";
import IconText from "~icons/vscode-icons/file-type-text";
import IconDocker from "~icons/vscode-icons/file-type-docker";
import IconDotenv from "~icons/vscode-icons/file-type-dotenv";
import IconGit from "~icons/vscode-icons/file-type-git";

import IconFolderSrc from "~icons/vscode-icons/folder-type-src";
import IconFolderSrcOpen from "~icons/vscode-icons/folder-type-src-opened";
import IconFolderImages from "~icons/vscode-icons/folder-type-images";
import IconFolderImagesOpen from "~icons/vscode-icons/folder-type-images-opened";
import IconFolderAsset from "~icons/vscode-icons/folder-type-asset";
import IconFolderAssetOpen from "~icons/vscode-icons/folder-type-asset-opened";
import IconFolderTest from "~icons/vscode-icons/folder-type-test";
import IconFolderTestOpen from "~icons/vscode-icons/folder-type-test-opened";
import IconFolderDocs from "~icons/vscode-icons/folder-type-docs";
import IconFolderDocsOpen from "~icons/vscode-icons/folder-type-docs-opened";
import IconFolderDist from "~icons/vscode-icons/folder-type-dist";
import IconFolderDistOpen from "~icons/vscode-icons/folder-type-dist-opened";
import IconFolderPublic from "~icons/vscode-icons/folder-type-public";
import IconFolderPublicOpen from "~icons/vscode-icons/folder-type-public-opened";
import IconFolderConfig from "~icons/vscode-icons/folder-type-config";
import IconFolderConfigOpen from "~icons/vscode-icons/folder-type-config-opened";
import IconFolderGit from "~icons/vscode-icons/folder-type-git";
import IconFolderGitOpen from "~icons/vscode-icons/folder-type-git-opened";
import IconFolderNode from "~icons/vscode-icons/folder-type-node";
import IconFolderNodeOpen from "~icons/vscode-icons/folder-type-node-opened";
import IconFolderVscode from "~icons/vscode-icons/folder-type-vscode";
import IconFolderVscodeOpen from "~icons/vscode-icons/folder-type-vscode-opened";

// Files without a normal extension, matched by their (lowercased) full name.
const SPECIAL_FILE_ICONS: Record<string, Component> = {
  dockerfile: IconDocker
};

// File extension (lowercased, without dot) -> icon component.
const EXT_ICONS: Record<string, Component> = {
  py: IconPython,
  go: IconGo,
  cpp: IconCpp,
  cc: IconCpp,
  cxx: IconCpp,
  c: IconC,
  h: IconCHeader,
  hpp: IconCppHeader,
  hxx: IconCppHeader,
  hh: IconCppHeader,
  js: IconJs,
  mjs: IconJs,
  cjs: IconJs,
  ts: IconTs,
  tsx: IconReactTs,
  jsx: IconReactJs,
  vue: IconVue,
  json: IconJson,
  yaml: IconYaml,
  yml: IconYaml,
  xml: IconXml,
  ini: IconIni,
  toml: IconToml,
  md: IconMarkdown,
  markdown: IconMarkdown,
  sh: IconShell,
  bash: IconShell,
  html: IconHtml,
  htm: IconHtml,
  css: IconCss,
  scss: IconScss,
  less: IconLess,
  sql: IconSql,
  txt: IconText,
  csv: IconText,
  dockerfile: IconDocker,
  env: IconDotenv,
  gitignore: IconGit
};

// Folder name (lowercased) -> closed/opened icon pair.
const FOLDER_ICONS: Record<string, { closed: Component; opened: Component }> = {
  src: { closed: IconFolderSrc, opened: IconFolderSrcOpen },
  images: { closed: IconFolderImages, opened: IconFolderImagesOpen },
  img: { closed: IconFolderImages, opened: IconFolderImagesOpen },
  assets: { closed: IconFolderAsset, opened: IconFolderAssetOpen },
  asset: { closed: IconFolderAsset, opened: IconFolderAssetOpen },
  test: { closed: IconFolderTest, opened: IconFolderTestOpen },
  tests: { closed: IconFolderTest, opened: IconFolderTestOpen },
  __tests__: { closed: IconFolderTest, opened: IconFolderTestOpen },
  docs: { closed: IconFolderDocs, opened: IconFolderDocsOpen },
  doc: { closed: IconFolderDocs, opened: IconFolderDocsOpen },
  dist: { closed: IconFolderDist, opened: IconFolderDistOpen },
  build: { closed: IconFolderDist, opened: IconFolderDistOpen },
  public: { closed: IconFolderPublic, opened: IconFolderPublicOpen },
  config: { closed: IconFolderConfig, opened: IconFolderConfigOpen },
  ".git": { closed: IconFolderGit, opened: IconFolderGitOpen },
  node_modules: { closed: IconFolderNode, opened: IconFolderNodeOpen },
  ".vscode": { closed: IconFolderVscode, opened: IconFolderVscodeOpen }
};

export function getFileIcon(fileName: string): Component {
  const lower = fileName.toLowerCase();
  if (lower in SPECIAL_FILE_ICONS) return SPECIAL_FILE_ICONS[lower];
  const dot = lower.lastIndexOf(".");
  const ext = dot >= 0 ? lower.slice(dot + 1) : "";
  return EXT_ICONS[ext] ?? IconDefaultFile;
}

export function getFolderIcon(folderName: string, expanded: boolean): Component {
  const pair = FOLDER_ICONS[folderName.toLowerCase()];
  if (pair) return expanded ? pair.opened : pair.closed;
  return expanded ? IconDefaultFolderOpened : IconDefaultFolder;
}
