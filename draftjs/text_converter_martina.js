import { stateFromHTML } from "draft-js-import-html";
import { JSDOM } from "jsdom";
import { readFile, writeFile } from "fs";
import { convertToRaw, EditorState } from "draft-js";
import { zipObject } from "lodash";
import { v4 as uuid } from "uuid";

global.document = new JSDOM(`...`).window.document;

const FromHTMLCustomBlockFn = element => {
  if (element.className === "callout") {
    return {
      type: "callout"
    };
  } else if (element.className === "discreet") {
    return {
      type: "discreet"
    };
  }
  return null;
};

const getId = () => Math.floor(Math.random() * Math.pow(2, 24)).toString(32);

const createCell = (type, value) => ({
  key: getId(),
  type: type,
  value: valueToDraft(value)
});

const valueToDraft = value => ({
  blocks: [
    {
      data: {},
      depth: 0,
      entityRanges: [],
      inlineStyleRanges: [],
      key: "co3kh",
      text: value,
      type: "unstyled"
    }
  ],
  entityMap: {}
});

const createTable = rows => ({
  basic: false,
  celled: true,
  compact: false,
  fixed: true,
  inverted: false,
  rows: rows,
  striped: false
});

const processInputData = (err, input) => {
  const dom = new JSDOM(input);
  const paragraphs = dom.window.document.body.children;
  const result = [];
  for (const paragraph of paragraphs) {
    let raw = {};
    const child = paragraph.firstElementChild;
    if (paragraph.tagName === "P" && child != null && child.tagName === "IMG") {
      // Images
      raw["@type"] = "image";
      raw.url = child.src;
      if (child.dataset.href != null) {
        raw.href = child.dataset.href;
      }
      if (child.className.indexOf("image-left") !== -1) {
        raw.align = "left";
      } else if (child.className.indexOf("image-right") !== -1) {
        raw.align = "right";
      } else if (child.className.indexOf("image-inline") !== -1) {
        raw.align = "full";
      }
    } else if (paragraph.tagName === "TABLE") {
      raw["@type"] = "table";
      const children = paragraph.children;
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
      raw.table = createTable(rows);
    } else if (paragraph.childElementCount !== 0) {
      for (const child of paragraph.children) {
        if (child.tagName === "SPAN") {
          debugger;
          const contentState = stateFromHTML(child.outerHTML, {
            customBlockFn: FromHTMLCustomBlockFn
          });
          const editorState = EditorState.createWithContent(contentState);
          _partial.text = convertToRaw(editorState.getCurrentContent());
        }
      }
    } else {
      // Normal paragraphs
      const contentState = stateFromHTML(paragraph.outerHTML, {
        customBlockFn: FromHTMLCustomBlockFn,
        processInlineElement: ProcessInlineElementFn
      });
      const editorState = EditorState.createWithContent(contentState);
      debugger;
      raw["@type"] = "text";
      if (Object.keys(_partial).length !== 0) {
        debugger;
      }
      raw.text = convertToRaw(editorState.getCurrentContent());
    }
    result.push(raw);
  }
  const jsonResult = zipObject(
    Array(result.length)
      .fill()
      .map(() => uuid()),
    result
  );
  console.log(JSON.stringify(jsonResult, null, 2));
  writeFile("test.json", JSON.stringify(jsonResult, null, 2), err => {});
};

// readFile('./text.html', { encoding: 'utf-8' }, processInputData);
console.log(process.argv);
readFile(process.argv[2], { encoding: "utf-8" }, processInputData);
