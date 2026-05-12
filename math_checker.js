const dataFromDB = {
  points: [171.57452400913473, 66.90848399599906, 166.62299143148442, 66.65736791601752],
  color: '#ee2689',
  lineWidth: 20
};

const parsePoints = (raw) => {
  if (!raw || !Array.isArray(raw)) return [];
  const pts = [];
  for (let i = 0; i < raw.length; i += 2) {
    pts.push({ x: raw[i], y: raw[i + 1] });
  }
  return pts;
};

const redrawSim = (stroke, cam) => {
  console.log("Simulating Redraw...");
  console.log("Camera:", cam);
  
  // Check data existence
  if (!stroke.data) { console.log("ERROR: no stroke data"); return; }
  
  const points = parsePoints(stroke.data.points);
  console.log("Parsed Points Count:", points.length);
  
  if (points.length < 1) { console.log("Early exit condition triggered"); return; }
  
  // Math check!
  console.log("MOVETO X:", points[0].x);
  console.log("MOVETO Y:", points[0].y);
  
  // Apply manual camera transform to verify final pixel coordinate simulation
  for (let i = 0; i < points.length; i++) {
    const screenX = (points[i].x * cam.zoom) + cam.x;
    const screenY = (points[i].y * cam.zoom) + cam.y;
    console.log(`Point ${i} final transformed screen coordinate: [${screenX}, ${screenY}]`);
    if (isNaN(screenX) || isNaN(screenY)) console.log("DETECTED NaN!!!");
  }
  console.log("Finished Sim successfully");
};

const fakeStroke = { data: dataFromDB };
const defaultCam = { x: 0, y: 0, zoom: 1 };

redrawSim(fakeStroke, defaultCam);
