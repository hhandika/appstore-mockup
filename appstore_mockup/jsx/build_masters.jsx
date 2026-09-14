// Builds layered Photoshop masters and flattened PNG exports from an
// appstore-mockup compose manifest. `appstore-mockup photoshop` runs it and
// passes the path of a job file as the first script argument.

var JOB_PATH = arguments[0];

function readJson(path) {
  var file = new File(path);
  file.encoding = "UTF-8";
  if (!file.open("r")) {
    throw new Error("Cannot open " + path);
  }
  var text = file.read();
  file.close();
  // ExtendScript predates JSON; the manifest is written by appstore-mockup.
  return eval("(" + text + ")");
}

function contains(items, value) {
  for (var i = 0; i < items.length; i++) {
    if (items[i] === value) {
      return true;
    }
  }
  return false;
}

function px(value) {
  return value.as("px");
}

function ensureFolder(path) {
  var folder = new Folder(path);
  if (!folder.exists && !folder.create()) {
    throw new Error("Cannot create " + path);
  }
  return folder;
}

function moveToTop(layer, parent) {
  if (parent.typename === "LayerSet" && parent.layers.length === 0) {
    layer.move(parent, ElementPlacement.INSIDE);
    return;
  }
  if (parent.layers[0].id !== layer.id) {
    layer.move(parent.layers[0], ElementPlacement.PLACEBEFORE);
  }
}

function addRaster(doc, parent, spec) {
  var source = app.open(new File(spec.file));
  var layer = source.activeLayer.duplicate(doc);
  source.close(SaveOptions.DONOTSAVECHANGES);
  app.activeDocument = doc;
  layer.name = spec.name;
  moveToTop(layer, parent);
  return layer;
}

function addSmartObject(doc, parent, spec) {
  app.activeDocument = doc;
  var descriptor = new ActionDescriptor();
  descriptor.putPath(charIDToTypeID("null"), new File(spec.file));
  descriptor.putEnumerated(
    charIDToTypeID("FTcs"),
    charIDToTypeID("QCSt"),
    charIDToTypeID("Qcsa")
  );
  executeAction(charIDToTypeID("Plc "), descriptor, DialogModes.NO);

  var layer = doc.activeLayer;
  var bounds = layer.bounds;
  var width = px(bounds[2]) - px(bounds[0]);
  var height = px(bounds[3]) - px(bounds[1]);
  layer.resize(
    (spec.box[2] / width) * 100,
    (spec.box[3] / height) * 100,
    AnchorPosition.TOPLEFT
  );
  bounds = layer.bounds;
  layer.translate(spec.box[0] - px(bounds[0]), spec.box[1] - px(bounds[1]));
  layer.name = spec.name;
  moveToTop(layer, parent);
  if (spec.clip) {
    layer.grouped = true;
  }
  return layer;
}

function addText(doc, parent, spec) {
  app.activeDocument = doc;
  var layer = doc.artLayers.add();
  layer.kind = LayerKind.TEXT;
  layer.name = spec.name;

  var item = layer.textItem;
  item.contents = spec.lines.join("\r");
  item.font = spec.font;
  item.size = new UnitValue(spec.size, "px");
  item.justification = Justification.CENTER;
  item.useAutoLeading = false;
  item.leading = new UnitValue(spec.leading, "px");
  item.tracking = spec.tracking;
  var color = new SolidColor();
  color.rgb.hexValue = spec.color.replace("#", "");
  item.color = color;
  item.position = [
    new UnitValue(spec.cx, "px"),
    new UnitValue(spec.ink_top + spec.size, "px"),
  ];

  // Align the inked block with the preview rather than the baseline.
  var bounds = layer.bounds;
  layer.translate(
    spec.cx - (px(bounds[0]) + px(bounds[2])) / 2,
    spec.ink_top - px(bounds[1])
  );
  moveToTop(layer, parent);
  return layer;
}

function addLayer(doc, parent, spec) {
  if (spec.kind === "group") {
    app.activeDocument = doc;
    var group = doc.layerSets.add();
    group.name = spec.name;
    moveToTop(group, parent);
    for (var i = 0; i < spec.layers.length; i++) {
      addLayer(doc, group, spec.layers[i]);
    }
    return group;
  }
  if (spec.kind === "smart") {
    return addSmartObject(doc, parent, spec);
  }
  if (spec.kind === "text") {
    return addText(doc, parent, spec);
  }
  return addRaster(doc, parent, spec);
}

function buildScreen(screen, job) {
  var doc = app.documents.add(
    new UnitValue(screen.canvas[0], "px"),
    new UnitValue(screen.canvas[1], "px"),
    72,
    screen.id,
    NewDocumentMode.RGB,
    DocumentFill.TRANSPARENT,
    1,
    BitsPerChannelType.EIGHT,
    "sRGB IEC61966-2.1"
  );
  var placeholder = doc.layers[0];
  for (var i = 0; i < screen.layers.length; i++) {
    addLayer(doc, doc, screen.layers[i]);
  }
  placeholder.remove();

  var psdOptions = new PhotoshopSaveOptions();
  psdOptions.layers = true;
  psdOptions.embedColorProfile = true;
  psdOptions.alphaChannels = false;
  var psdFolder = ensureFolder(job.psd_dir);
  doc.saveAs(
    new File(psdFolder.fullName + "/" + screen.id + ".psd"),
    psdOptions,
    true,
    Extension.LOWERCASE
  );

  // Store uploads must not carry transparency, so export a flattened copy.
  var flat = doc.duplicate(screen.id + " flat");
  flat.flatten();
  var pngOptions = new PNGSaveOptions();
  pngOptions.compression = 6;
  pngOptions.interlaced = false;
  var pngFolder = ensureFolder(job.png_dir);
  flat.saveAs(
    new File(pngFolder.fullName + "/" + screen.id + ".png"),
    pngOptions,
    true,
    Extension.LOWERCASE
  );
  flat.close(SaveOptions.DONOTSAVECHANGES);
  doc.close(SaveOptions.DONOTSAVECHANGES);
}

function main() {
  var job = readJson(JOB_PATH);
  var manifest = readJson(job.manifest);
  var saved = {
    rulerUnits: app.preferences.rulerUnits,
    typeUnits: app.preferences.typeUnits,
    dialogs: app.displayDialogs,
  };
  app.preferences.rulerUnits = Units.PIXELS;
  app.preferences.typeUnits = TypeUnits.PIXELS;
  app.displayDialogs = DialogModes.NO;

  var built = [];
  var failure = null;
  for (var i = 0; i < manifest.screens.length; i++) {
    var screen = manifest.screens[i];
    if (job.only.length && !contains(job.only, screen.id)) {
      continue;
    }
    try {
      buildScreen(screen, job);
      built.push(screen.id);
    } catch (error) {
      failure = screen.id + ": " + error.message + " (line " + error.line + ")";
      break;
    }
  }

  app.preferences.rulerUnits = saved.rulerUnits;
  app.preferences.typeUnits = saved.typeUnits;
  app.displayDialogs = saved.dialogs;
  if (failure) {
    throw new Error(failure);
  }
  return "Built " + built.length + " master(s): " + built.join(", ");
}

main();
