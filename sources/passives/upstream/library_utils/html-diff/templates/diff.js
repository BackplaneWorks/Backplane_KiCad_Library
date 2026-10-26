const kicadLayers = [
    "Names", "Hole_Plated", "Hole_Nonplated",
    "F_Cu", "B_Cu",
    "F_Fab", "B_Fab",
    "F_SilkS", "B_SilkS",
    "F_Paste", "B_Paste",
    "F_Mask", "B_Mask",
    "F_CrtYd", "B_CrtYd",
    "F_Adhes", "B_Adhes",
    "Dwgs_User", "Cmts_User",
    "Eco1_User", "Eco2_User",
    "Edge_Cuts", "Margin",
    "User_1", "User_2", "User_3", "User_4", "User_5", "User_6", "User_7", "User_8", "User_9" ];

let layerSets = {
    all: kicadLayers,
    top: [ "Names", "Hole_Plated", "Hole_Nonplated", "F_Cu", "F_Adhes", "F_Paste", "F_SilkS", "F_Mask",
        "Dwgs_User", "Cmts_User", "Eco1_User", "Eco2_User", "Edge_Cuts", "Margin", "F_CrtYd", "F_Fab"],
    bottom: [ "Names", "Hole_Plated", "Hole_Nonplated", "B_Cu", "B_Adhes", "B_Paste", "B_SilkS", "B_Mask",
        "Dwgs_User", "Cmts_User", "Eco1_User", "Eco2_User", "Edge_Cuts", "Margin", "B_CrtYd", "B_Fab"],
    mech: [ "Hole_Plated", "Hole_Nonplated", "Edge_Cuts", "Margin", "F_CrtYd", "B_CrtYd", "F_Fab", "B_Fab"],
    graph: [ "F_SilkS", "B_SilkS", "Dwgs_User", "Cmts_User", "Eco1_User", "Eco2_User", "Margin", "F_CrtYd",
            "B_CrtYd", "F_Fab", "B_Fab", "User_1", "User_2", "User_3", "User_4", "User_5", "User_6",
            "User_7", "User_8", "User_9" ],
};

class Colorscheme {
    svgStyle(layers=kicadLayers) {
        let defs = ['* { fill: none; stroke: none; } tspan { fill: inherit; }'];
        for (const layer of layers) {
            if (layer in this) {
                defs.push(`.l-${layer}-f { fill: ${this[layer]}; fill-opacity: 0.25; }`);
                defs.push(`.l-${layer}-s { stroke: ${this[layer]}; }`);
            } else {
                defs.push(`.l-${layer}-f, .l-${layer}-s { fill: none; stroke: none; }`);
            }
        }
        defs.push(`.l-any-f { fill: ${this["F_Cu"]}; }`);
        defs.push(`.l-any-s { stroke: ${this["F_Cu"]}; }`);
        return defs.join("\n\n");
    }
}

class DefaultColorscheme extends Colorscheme {
    Names               = "rgb(200, 200, 200)";
    Hole_Plated         = "rgb(194, 194, 0)";
    Hole_Nonplated      = "rgb(26,  196, 210)";
    F_Cu        = "rgb(200, 52,  52)";
    B_Cu        = "rgb(77,  127, 196)";
    F_Adhes     = "rgb(132, 0, 132)";
    B_Adhes     = "rgb(0,   0, 132)";
    F_Paste     = "rgb(162, 144, 139)";
    B_Paste     = "rgb(0,   175, 175)";
    F_SilkS     = "rgb(242, 237, 161)";
    B_SilkS     = "rgb(232, 178, 167)";
    F_Mask      = "rgb(86,  40,  102)";
    B_Mask      = "rgb(1,   102, 95)";
    Dwgs_User   = "rgb(194, 194, 194)";
    Cmts_User   = "rgb(89,  148, 220)";
    Eco1_User   = "rgb(180, 219, 210)";
    Eco2_User   = "rgb(216, 200, 82)";
    Edge_Cuts   = "rgb(208, 210, 205)";
    Margin      = "rgb(255, 38,  226)";
    F_CrtYd     = "rgb(255, 38,  226)";
    B_CrtYd     = "rgb(38,  233, 255)";
    F_Fab       = "rgb(175, 175, 175)";
    B_Fab       = "rgb(88,  93,  132)";
    User_1      = "rgb(194, 194, 194)";
    User_2      = "rgb(89,  148, 220)";
    User_3      = "rgb(180, 219, 210)";
    User_4      = "rgb(216, 200, 82)";
    User_5      = "rgb(194, 194, 194)";
    User_6      = "rgb(89,  148, 220)";
    User_7      = "rgb(180, 219, 210)";
    User_8      = "rgb(216, 200, 82)";
    User_9      = "rgb(232, 178, 167)";
}

class MonochromeColorscheme extends Colorscheme {
    constructor(color) {
        super();
        for (const key of kicadLayers) {
            this[key] = color;
        }
    }
}

class DragArea {
    renderOffX = 0;
    renderOffY = 0;
    renderZoom = 1.0;
    /* mouse event handling */
    downX = 0;
    downY = 0;
    mouseDeltaX = 0;
    mouseDeltaY = 0;
    mouseX = 0;
    mouseY = 0;
    diffMode = false;
    hideText = false;
    diffGreenIndex = 1;
    colorscheme;

    constructor(containerId, colorscheme=null, diffMode=false, hideText=false) {
        this.colorscheme = colorscheme;
        this.diffMode = diffMode;
        this.hideText = hideText;
        this.container = document.getElementById(containerId);
        this.canvas = document.createElement('canvas');
        this.container.appendChild(this.canvas);
        this.resizeObserver = new ResizeObserver((entries) => {
            this.canvas.width = entries[0].contentRect.width;
            this.canvas.height = entries[0].contentRect.height;
            this.refresh();
        });
        this.resizeObserver.observe(this.container);
        this.images = [];
        this.imagesProcessed = [];
        this.imagesVisible = [];
        document.addEventListener('keydown', this.keydown.bind(this));
        this.canvas.addEventListener('mousedown', this.mousedown.bind(this));
        this.canvas.addEventListener('mousemove', this.mousemove.bind(this));
        this.canvas.addEventListener('wheel', this.wheel.bind(this));
    }

    refresh() {
        window.requestAnimationFrame(this.refreshCanvas.bind(this));
    }

    setImages(arr) {
        this.images = arr;
        this.refreshImages();
    }

    setImagesVisible(imagesVisible) {
        this.imagesVisible = imagesVisible;
        this.refresh();
    }

    refreshImages() {
        this.imagesProcessed = [];

        for (let [index, svgText] of this.images.entries()) {
            try {
                const parser = new DOMParser();
                const svgDocument = parser.parseFromString(svgText, 'image/svg+xml');
                const styleElem = svgDocument.createElementNS('http://www.w3.org/2000/svg', 'style');

                let style = "";
                let colorscheme = this.colorscheme;
                if (colorscheme !== null) {
                    if (this.diffMode) {
                        colorscheme = new MonochromeColorscheme(index < this.diffGreenIndex ? '#00ff00' : '#ff0000');
                    }

                    style = colorscheme.svgStyle(kicadLayers.filter(
                            layer => layerSelCheckboxes[layer].checked));

                    if (this.hideText) {
                        style += "text { display: none; }\n\n";
                    }
                }

                styleElem.appendChild(svgDocument.createTextNode(`\n${style}\n`));
                svgDocument.querySelector('svg').prepend(styleElem);
                const serializer = new XMLSerializer();
                const blob = new Blob([serializer.serializeToString(svgDocument)], {type: 'image/svg+xml'});
                console.log(serializer.serializeToString(svgDocument));
                const blobURL = URL.createObjectURL(blob);
                let imageElement = new Image();
                imageElement.src = blobURL;
                imageElement.addEventListener('load', event => {
                    URL.revokeObjectURL(blobURL);
                    this.imagesProcessed.push(imageElement);
                    this.refresh();
                }, {once: true});
            } catch (error) {
            }
        }
    }

    *alignImages() {
        let maxW = 0;
        let maxH = 0;
        for (const img of this.imagesProcessed) {
            var iw = img.naturalWidth;
            var ih = img.naturalHeight;
            if (iw > maxW) {
                maxW = iw;
            }
            if (ih > maxH) {
                maxH = ih;
            }
        }

        let sx = this.canvas.width / maxW;
        let sy = this.canvas.height / maxH;
        let scale = Math.min(sx, sy);

        for (const img of this.imagesProcessed) {
            let iw = img.naturalWidth;
            let ih = img.naturalHeight;
            let rw = iw*scale;
            let rh = ih*scale;
            let x = this.canvas.width/2 - rw/2;
            let y = this.canvas.height/2 - rh/2;
            yield [x, y, rw, rh, img];
        }
    }

    imageBounds() {
        var [minX, minY] = [Infinity, Infinity];
        var [maxX, maxY] = [-Infinity, -Infinity];
        for (const [x, y, rw, rh, img] of this.alignImages()) {
            if (x < minX) {
                minX = x;
            }
            if (y < minY) {
                minY = y;
            }
            if (x+rw > maxX) {
                maxX = x+rw;
            }
            if (y+rh > maxY) {
                maxY = y+rh;
            }
        }
        return [minX, minY, maxX-minX, maxY-minY];
    }

    refreshCanvas() {
        console.log('refresh', this.imagesVisible);
        var ctx = this.canvas.getContext('2d');
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        if (this.diffMode) {
            ctx.globalCompositeOperation = 'screen';
        }

        let idx = 0;
        for (const [x, y, rw, rh, img] of this.alignImages()) {
            if (this.imagesVisible.includes(idx)) {
                var cx = this.canvas.width/2;
                var cy = this.canvas.height/2;
                var ix = cx + (x - cx)*this.renderZoom;
                var iy = cy + (y - cy)*this.renderZoom;
                var ox = this.renderOffX + this.mouseDeltaX;
                var oy = this.renderOffY + this.mouseDeltaY;
                ctx.drawImage(img, ix+ox, iy+oy, rw*this.renderZoom, rh*this.renderZoom);
            }
            idx++;
        }
    }

    keydown(event) {
        if (event.key == 'Home') {
            this.renderOffX = 0;
            this.renderOffY = 0;
            this.mouseDeltaX = 0;
            this.mouseDeltaY = 0;
            this.renderZoom = 1.0;
            this.refresh();
        }
    }

    mousedown(event) {
        this.renderOffX += this.mouseDeltaX;
        this.renderOffY += this.mouseDeltaY;
        this.mouseDeltaX = 0;
        this.mouseDeltaY = 0;
        this.downX = event.clientX;
        this.downY = event.clientY;
    }

    mousemove(event) {
        if (event.buttons & 1) { /* primary button pressed */
            /* We can't use movementX/movementY here since they drift. */
            this.mouseDeltaX = event.clientX - this.downX;
            this.mouseDeltaY = event.clientY - this.downY;

            const [x, y, rw, rh] = this.imageBounds();
            const boundsX = this.canvas.width/2*0.9 + rw*this.renderZoom/2;
            const boundsY = this.canvas.height/2*0.9 + rh*this.renderZoom/2;

            var ox = Math.max(Math.min(this.renderOffX+this.mouseDeltaX, boundsX), -boundsX);
            var oy = Math.max(Math.min(this.renderOffY+this.mouseDeltaY, boundsY), -boundsY);
            this.mouseDeltaX = ox-this.renderOffX;
            this.mouseDeltaY = oy-this.renderOffY;

            this.refresh();
        }
        var rect = this.canvas.getBoundingClientRect();
        this.mouseX = event.clientX - rect.left;
        this.mouseY = event.clientY - rect.top;
    }

    wheel(event) {
        const minZoom = 0.1;
        const maxZoom = 10;
        const zoomBase = 1.1;
        const zoomDiv = 256.0;
        var zoomFactor = Math.pow(zoomBase, -event.deltaY/zoomDiv);
        var oldRenderZoom = this.renderZoom;
        this.renderZoom *= zoomFactor;
        this.renderZoom = Math.min(maxZoom, Math.max(minZoom, this.renderZoom));
        var actualZoomFactor = this.renderZoom / oldRenderZoom;

        var cx = this.canvas.width / 2;
        var cy = this.canvas.height / 2;

        this.renderOffX += this.mouseDeltaX;
        this.renderOffY += this.mouseDeltaY;
        this.mouseDeltaX = 0;
        this.mouseDeltaY = 0;

        this.renderOffX = (this.renderOffX - (this.mouseX-cx))*actualZoomFactor + (this.mouseX-cx);
        this.renderOffY = (this.renderOffY - (this.mouseY-cy))*actualZoomFactor + (this.mouseY-cy);

        this.refresh();
    }
}

const dragRender = new DragArea('fp-render');
dragRender.setImages(svg_ref);

const colorscheme = new DefaultColorscheme();
const dragLayerView = new DragArea('fp-layer-view', colorscheme);
dragLayerView.setImages(svg_new);

const dragDiff = new DragArea('fp-visual-diff', colorscheme, true, hideTextInDiff);
dragDiff.setImages(svg_new.concat(svg_old));
dragDiff.diffGreenIndex = svg_new.length;

function refreshImages() {
    dragDiff.refreshImages();
    dragRender.refreshImages();
    dragLayerView.refreshImages();
}


function checkboxForLayer(layer) {
    const checkbox = document.getElementById(`layer-sel-${layer}`);
    return checkbox;
}


const layerSelDiv = document.getElementById("layer-sel");
const layerDrawer = document.getElementById("layer-drawer");
let layerSelCheckboxes = {};

/**
 * Refresh the group checkboxes for layer sets based on the current state of the
 * individual layer checkboxes.
 */
function refreshLayerSetCheckboxes() {
    for (const [name, layerSet] of Object.entries(layerSets)) {
        const checkbox = checkboxForLayer(name);
        const checked = layerSet.filter(layer => layerSelCheckboxes[layer].checked);
        if (checked.length == 0) {
            checkbox.checked = false;
            checkbox.indeterminate = false;
        } else if (checked.length == layerSet.length) {
            checkbox.checked = true;
            checkbox.indeterminate = false;
        } else {
            checkbox.checked = true;
            checkbox.indeterminate = true;
        }
    }
    refreshImages();
}

/**
 * Persist the current layer selection to localStorage.
 */
function persistLayerSelection() {
    const layerSelection = {};
    for (const layerCb of Object.values(layerSelCheckboxes)) {
        layerSelection[layerCb.id] = layerCb.checked;
    }
    localStorage.setItem('layerCbSelection', JSON.stringify(layerSelection));
}

/**
 * Attempt to load the layer selection from localStorage.
 */
function loadLayerSelection() {
    const layerSelection = localStorage.getItem('layerCbSelection');
    if (layerSelection) {
        const parsedSelection = JSON.parse(layerSelection);
        for (const [layerId, checked] of Object.entries(parsedSelection)) {
            const checkbox = document.getElementById(layerId);
            if (checkbox) {
                checkbox.checked = checked;
            }
        }
    }
    refreshLayerSetCheckboxes();
}


function onLayerCbClick(event, layers) {
    // Ctrl click: turn this layer on and turn off all others
    if (event.ctrlKey) {
        for (const [layerName, layerCb] of Object.entries(layerSelCheckboxes)) {
            if (layers.includes(layerName)) {
                layerCb.checked = true;
            }
            else
            {
                layerCb.checked = false;
            }
        }
    }
    else
    {
        const checked = event.target.checked;
        for(const layerName of layers) {
            const layerCb = layerSelCheckboxes[layerName];
            layerCb.checked = checked;
        }
    }
}

// Separate change handler to click handler to catch changes that are not caused by clicks
function onLayerCbChange(event) {
    refreshLayerSetCheckboxes();
    persistLayerSelection();
}


for (const [name, layerSet] of Object.entries(layerSets)) {
    const checkbox = checkboxForLayer(name);
    checkbox.addEventListener('click', event => {
        onLayerCbClick(event, layerSet);
    });
    checkbox.addEventListener('change', onLayerCbChange);
    checkbox.title = `Ctrl+click to select only this layer set.`;
}

for (const layer of kicadLayers) {
    const div = document.createElement("div");
    const input = document.createElement("input");
    input.id = `layer-sel-${layer}`;
    input.type = "checkbox";
    input.checked = true;
    const label = document.createElement("label");
    label.setAttribute("for", input.id);
    label.appendChild(document.createTextNode(layer.replace("_", ".")));
    div.appendChild(input);
    div.appendChild(label);
    layerSelDiv.appendChild(div);
    layerSelCheckboxes[layer] = input;
    input.addEventListener('click', event => {
        onLayerCbClick(event, [layer]);
    });
    input.addEventListener('change', onLayerCbChange);
    input.title = `Ctrl+click to select only this layer.`;
}

loadLayerSelection();

const unit_sel = document.getElementById('unit-sel');
const unitButtons = unit_sel.querySelectorAll('.unit-button');

if (unitButtons.length > 1) {
    /* Create unit selection list */
    for (const button of unitButtons) {
        const u = parseInt(button.getAttribute('data-unit'));
        button.addEventListener('click', event => setUnit(u));
    }
} else {
    unit_sel.style = 'display: none';
}

function setUnit(newUnit) {
    console.log('setUnit', newUnit);
    dragRender.setImagesVisible([newUnit]);
    dragLayerView.setImagesVisible([newUnit]);
    dragDiff.setImagesVisible([newUnit, svg_new.length+newUnit]);

    if (unitButtons.length > 1) {
        unitButtons.forEach(btn => btn.classList.remove('selected'));
        unitButtons[newUnit].classList.add('selected');
    }
}
setUnit(0);

refreshLayerSetCheckboxes();

if (enableLayers) {
    document.getElementById('btn-layer-view').style = 'display: initial';
} else {
    document.getElementById('btn-layer-view').style = 'display: none';
    document.getElementById('layer-drawer').classList.add('hidden');
}

if (svg_ref.length > 0) {
    if (!window.location.hash) {
        window.location.hash = '#render';
    }
} else {
    if (!window.location.hash) {
        window.location.hash = '#layer-view';
    }
    document.getElementById('btn-render').style = 'display: none';
}


function updateIndexLinkHashes() {
    const newHash = window.location.hash;

    const updateHrefHash = (elem) => {
        const url = new URL(elem.href);
        url.hash = newHash;
        elem.href = url.toString();
    };

    // Top left navigation buttons
    for (const elem_id of ['nav-bt-prev', 'nav-bt-next']) {
        const bt = document.getElementById(elem_id);
        if (bt) {
            updateHrefHash(bt);
        }
    }

    // Enable the layer drawer if the view can use it
    const hasLayerDrawer = enableLayers && ['#visual-diff', '#layer-view'].includes(newHash);
    const layerDrawer = document.getElementById('layer-drawer');
    layerDrawer.classList.toggle('hidden', !hasLayerDrawer);

    // Highlight the active sidebar button
    const sidebarButtons = document.querySelectorAll('.sidebar > a');
    sidebarButtons.forEach(btn => btn.classList.remove("selected"));

    const activeBtn = document.querySelector(`.sidebar > a[href="${newHash}"]`);
    if (activeBtn) {
        activeBtn.classList.add("selected");
    }

    // Update index pane links
    const indexList = document.getElementById('index');
    for (const link of indexList.querySelectorAll('a')) {
        updateHrefHash(link);
    }
}

window.addEventListener('hashchange', event => {
    updateIndexLinkHashes();
});

updateIndexLinkHashes();

document.getElementById('index-button').addEventListener('click', event => {
    document.getElementById('index').classList.toggle('index-bt-toggle');
});


function findDatasheet() {
    const propTable = document.getElementById('properties-table');

    // Find the link in the third col (the newer part)
    let datasheetLink = propTable.querySelector('td:nth-child(3) a');

    if (!datasheetLink) {
        // Try the second col
        datasheetLink = propTable.querySelector('td:nth-child(2) a');
    }

    return datasheetLink;
}


const datasheet = findDatasheet();

if (datasheet) {

    document.getElementById('datasheet-button').addEventListener('click', event => {

        // Open the link in a new tab
        window.open(datasheet.href, '_blank');
    } );
} else {
    document.getElementById('datasheet-button').disabled = true;
    document.getElementById('datasheet-button').title = "No datasheet found (d)";
}

// listen for all keydown events
document.getElementById('body').addEventListener('keydown', event => {
    let eId = null;

    // These keys only apply for un-modified key presses
    // (e.g. don't trigger when Ctrl+C is pressed to copy text)
    if (!event.ctrlKey && !event.altKey && !event.metaKey) {
        switch (event.key) {
            case "ArrowLeft":
                eId = "nav-bt-prev"
                break;
            case "ArrowRight":
                eId = "nav-bt-next"
                break;
            case "c":
                eId = "btn-code-diff";
                break;
            case "l":
                eId = "btn-layer-view";
                break;
            case "m":
                eId = "btn-metadata";
                break;
            case "r":
                eId = "btn-render";
                break;
            case "v":
                eId = "btn-visual-diff";
                break;
            case "d":
                eId = "datasheet-button";
                break;
            case "i":
                eId = "index-button";
                break;
        }
    }

    // Click the link if we can find one for this key
    if (eId) {
        const lnk = document.getElementById(eId);
        if (lnk) {
            lnk.click();
        }
    }
});

// Make sure the current link is visible in the index
const indexSelf = document.querySelector('.index-self');
if (indexSelf) {
    indexSelf.scrollIntoView({ block: 'nearest' });
}
