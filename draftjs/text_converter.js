import { stateFromHTML } from "draft-js-import-html";
import { convertToRaw, EditorState } from "draft-js";
import { JSDOM } from "jsdom";
import { readFile, writeFile } from "fs";

const FromHTMLCustomBlockFn = (element) => {
  if (element.className === "callout") {
    return {
      type: "callout",
    };
  }
  return null;
};

const getId = () => Math.floor(Math.random() * Math.pow(2, 24)).toString(32);

const createCell = (type, value) => ({
  key: getId(),
  type: type,
  value: valueToDraft(value),
});

const valueToDraft = (value) => ({
  blocks: [
    {
      data: {},
      depth: 0,
      entityRanges: [],
      inlineStyleRanges: [],
      key: getId(),
      text: value,
      type: "unstyled",
    },
  ],
  entityMap: {},
});

const createTable = (rows) => ({
  basic: false,
  celled: true,
  compact: false,
  fixed: true,
  inverted: false,
  rows: rows,
  striped: false,
});

global.document = new JSDOM(`...`).window.document;
const debug = process.env.NODE_ENV === "development";

const getYTVideoId = (url) => {
  let id = "";
  url = url
    .replace(/(>|<)/gi, "")
    .split(/(vi\/|v=|\/v\/|youtu\.be\/|\/embed\/)/);
  if (url[2] !== undefined) {
    id = url[2].split(/[^0-9a-z_\-]/i);
    id = id[0];
  }
  return id;
};

const generateImageBlock = (elem) => {
  let block = {};
  block["@type"] = "image";
  block.url = elem.src;
  if (elem.dataset.href != null) {
    block.href = elem.dataset.href;
  }
  if (elem.className.indexOf("image-left") !== -1) {
    block.align = "left";
  } else if (elem.className.indexOf("image-right") !== -1) {
    block.align = "right";
  } else if (elem.className.indexOf("image-inline") !== -1) {
    block.align = "center";
  }
  return block;
};

const generateIframeBlock = (elem) => {
  let youtubeId = getYTVideoId(elem.src);
  if (youtubeId.length == 0) {
    //  not a youtube video
    return generateStandardBlock(elem);
  }
  let block = {};
  block["@type"] = "video";
  block.url = "https://youtu.be/" + youtubeId;
  return block;
};

const generateTableBlock = (elem) => {
  let block = {};
  block["@type"] = "table";
  const children = elem.children;
  let rows = [];
  // recursive search for reconstructing table
  for (const table of children) {
    for (const tchild of table.children) {
      if (tchild.tagName === "TR") {
        let cells = [];
        for (const cell of tchild.children) {
          cells.push(createCell("data", cell.textContent));
        }
        rows.push({ cells });
      }
    }
  }
  block.table = createTable(rows);
  return block;
};

const generateStandardBlock = (elem) => {
  let block = {};
  const contentState = stateFromHTML(elem.outerHTML, {
    customBlockFn: FromHTMLCustomBlockFn,
  });
  const editorState = EditorState.createWithContent(contentState);
  block["@type"] = "text";
  block.text = convertToRaw(editorState.getCurrentContent());
  return block;
};

const processInputData = (err, input) => {
  const dom = new JSDOM(input);
  const paragraphs = dom.window.document.body.children;
  const result = [];
  for (const paragraph of paragraphs) {
    let raw = {};
    const child = paragraph.firstElementChild;
    if (paragraph.tagName === "P") {
      if (child != null) {
        switch (child.tagName) {
          case "IMG":
            raw = generateImageBlock(child);
            break;
          case "TABLE":
            raw = generateTableBlock(child);
            break;
          case "IFRAME":
            raw = generateIframeBlock(child);
            break;
          default:
            raw = generateStandardBlock(paragraph);
            break;
        }
      } else {
        raw = generateStandardBlock(paragraph);
      }
    } else {
      switch (paragraph.tagName) {
        case "TABLE":
          raw = generateTableBlock(paragraph);
          break;
        case "IFRAME":
          raw = generateIframeBlock(paragraph);
          break;
        default:
          raw = generateStandardBlock(paragraph);
          break;
      }
    }
    result.push(raw);
  }
  writeFile(
    debug ? `${process.argv[2]}.json` : process.argv[2],
    JSON.stringify(result),
    (err) => {}
  );
};

readFile(process.argv[2], { encoding: "utf-8" }, processInputData);
