const { spawn } = require('child_process');

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
    const pyscript = spawn('python3', ['autoReservation.py']);
    pyscript.stdout.on('data', (data) => {
        console.log(`output: ${data}`);
        if(data == "DONE"){
            success()
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
    var button = document.getElementById('autoReservationBtn');
      // Change the button content
      button.innerHTML = 'Reservation Complete<span aria-hidden>_</span><span aria-hidden class="cybr-btn__glitch">Completed_</span><span aria-hidden class="cybr-btn__tag">R26</span>';
      button.style.backgroundColor = 'green';
    
}
function failiur(){
    var button = document.getElementById('autoReservationBtn');
    // Change the button content
    button.innerHTML = `<button id="autoReservationBtn" class="cybr-btn">
    Automatic Reservation_<span aria-hidden>_</span>
    <span aria-hidden class="cybr-btn__glitch">UCY GYM_</span>
    <span aria-hidden class="cybr-btn__tag">R25</span>
  </button>`;
    button.style.backgroundColor = 'red';
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