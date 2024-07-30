const { spawn } = require('child_process');
var ReservationTime = 1;

function firstTime(){
    const pyscript = spawn('python3', ['firstTime.py']);
    pyscript.stdout.on('data', (data) => {
        console.log(`output: ${data}`);
    });

    pyscript.stderr.on('data', (data) => {
        console.error(`error: ${data}`);
    });

    pyscript.on('close', (code) => {
        console.log(`script exited with code ${code}`);
    });
}
function autoReservation(){
    const pyscript = spawn('python3', ['autoReservation.py', ReservationTime]);
    pyscript.stdout.on('data', (data) => {
        console.log(`output: ${data}`);
        if(data.includes("DONE")){
            success();
        }
        
    });

    pyscript.stderr.on('data', (data) => {
        console.error(`error: ${data}`);
        if (data.includes("ERROR")) {
            failiur();
        }

    });

    pyscript.on('close', (code) => {
        console.log(`script exited with code ${code}`);
    });
}
function success(){
    var button = document.getElementById('Result');
      // Change the button content
      button.innerHTML = 'Reservation Complete<span aria-hidden>_</span><span aria-hidden class="cybr-btn__glitch">Completed_</span><span aria-hidden class="cybr-btn__tag">R26</span>';
      button.style.backgroundColor = 'green';
    
}
function failiur(){
    console.log("failiur")
    var button = document.getElementById('Result');
    if (button) {
        // Create a new button element
        const newButton = document.createElement('button');
        newButton.id = 'autoReservationBtn';
        newButton.className = 'cybr-btn';
        newButton.innerHTML = `Reservation Not Complete<span aria-hidden>_</span>
          <span aria-hidden class="cybr-btn__glitch">!!!!!!!!!!!!!!!!!</span>
          <span aria-hidden class="cybr-btn__tag">R26</span>`;
        newButton.style.backgroundColor = 'red';
        // Replace the old button with the new one
        button.parentNode.replaceChild(newButton, button);
      }
}

function setTime(resTime){
    //send the resTime to py script
    ReservationTime=resTime
}

// Example usage: Call autoReservation when needed
// autoReservation();  // Uncomment to call immediately
// Or attach to an event listener
document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('autoReservationBtn');
    if (button) {
      button.addEventListener('click', autoReservation);
    }
  });

