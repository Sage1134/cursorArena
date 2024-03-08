let cursors = {}
let isDrawing = false;
let previousX, previousY;

document.addEventListener("DOMContentLoaded", function() {
  const isLocalConnection = window.location.hostname === '10.0.0.138';
  const socket = new WebSocket(isLocalConnection ? 'ws://10.0.0.138:1134' : 'ws://99.245.65.253:1134');

  socket.onopen = function(event) {
    const arena = document.getElementById("arena");

    const clearButton = document.getElementById("clear");
    clearButton.addEventListener("click", function() {
      socket.send(JSON.stringify({ purpose: "clear" }));
    })

    arena.addEventListener("mousedown", function(event) {
      delete previousX;
      delete previousY;
  
      isDrawing = true;
      const localX = event.offsetX;
      const localY = event.offsetY;
  
      previousX = localX;
      previousY = localY;
      socket.send(JSON.stringify({ purpose: "draw", x1: previousX, y1: previousY, x2: localX, y2: localY }));
    })
  
    arena.addEventListener("mousemove", function(event) {
      const localX = event.offsetX;
      const localY = event.offsetY;

      socket.send(JSON.stringify({ purpose: "move", x: localX, y: localY }));

      if (!isDrawing) return;

      socket.send(JSON.stringify({ purpose: "draw", x1: previousX, y1: previousY, x2: localX, y2: localY }));
      
      previousX = localX;
      previousY = localY;
    })
  
    document.addEventListener("mouseup", function(event) {
      isDrawing = false;
    })
  
    arena.addEventListener("mouseleave", function() {
      delete previousX;
      delete previousY;
    })
  
    arena.addEventListener("mouseenter", function(event) {
      previousX = event.offsetX;
      previousY = event.offsetY;
    })
  
    function draw(startX, startY, endX, endY, cursorColor, ctx) {
      ctx.lineWidth = 4;
      ctx.strokeStyle = cursorColor;
      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.lineTo(endX, endY);
      ctx.stroke();
      ctx.closePath();
  }
  
    
    function clearArena() {
      arena.getContext("2d").clearRect(0, 0, arena.width, arena.height);
    }
    
    socket.addEventListener("message", function(event) {
      const jsonObject = JSON.parse(event.data);
      if (jsonObject.purpose === "move") {
        if (!cursors[jsonObject.sender]) {
          createCursor(jsonObject.sender);
        }
    
        const x = jsonObject.x;
        const y = jsonObject.y;
        updateCursor(jsonObject.sender, x, y);
      }
      
      else if (jsonObject.purpose === "draw") {
        draw(jsonObject.x1, jsonObject.y1, jsonObject.x2, jsonObject.y2, cursors[jsonObject.sender].color, arena.getContext("2d"));
      }
      
      else if (jsonObject.purpose === "load") {
        for (let y = 0; y < jsonObject.data.length; y++) {
          for (let x = 0; x < jsonObject.data[y].length; x++) {
            if (jsonObject.data[y][x] !== 0) {
              drawPixel(x, y, "black", arena.getContext("2d"));
            }
          }
        }
      }
      
      else if (jsonObject.purpose === "clear") {
        clearArena();
      }
      
      else if (jsonObject.purpose === "disconnect") {
        document.body.removeChild(cursors[jsonObject.client].element);
        delete cursors[jsonObject.client];
      }
    });

    function createCursor(sender) {
      const cursor = document.createElement("div");
      cursor.className = "cursor";
      const color = getRandomColor();
      cursor.style.backgroundColor = color;
      document.body.appendChild(cursor);
      cursors[sender] = { element: cursor, color: color };
    }
    
    function updateCursor(sender, x, y) {
      const cursorData = cursors[sender];
    
      if (cursorData) {
        const cursor = cursorData.element;
        const color = cursorData.color;
    
        const arenaRect = arena.getBoundingClientRect();
        cursor.style.left = (x + arenaRect.left + 1) + "px";
        cursor.style.top = (y + arenaRect.top + 1) + "px";
        cursor.style.backgroundColor = color;
      }
    }
  }

  function drawPixel(x, y, color, ctx) {
    ctx.fillStyle = color;
  
    const centerX = x + 0.5;
    const centerY = y + 0.5;
    const radiusX = 1;
    const radiusY = 1;
  
    ctx.beginPath();
    ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI);
    ctx.fill();
    ctx.closePath();
  }

  function getRandomColor() {
    const letters = "0123456789ABCDEF";
    let color = "#";
    for (let i = 0; i < 6; i++) {
      color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
  }
})