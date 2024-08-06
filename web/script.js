const { spawn } = require('child_process');
const path = require('path');
var ReservationTime = 1;//default time (7:45).
let currentDate =1;//default day date 1/current
let status=false; //whether the animation will continue or not.

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
    var flag=false;
    var counter=0;
    pleaseWaitAnimation();
    const pyscript = spawn('python3', ['autoReservation.py', ReservationTime, currentDate]);
    pyscript.stdout.on('data', (data) => {
        console.log(`output: ${data}`);
        if(data.includes("DONE")){
            success();
        }
        
    });

    pyscript.stderr.on('data', (data) => {
        console.error(`error: ${data}`);
        if(data.includes)
        if (data.includes("ERROR")) {
            failiur();
            flag=true;
        }
        if(data.includes("/6") && flag==false){
            loading(counter);
            counter++;
        }
    });

    pyscript.on('close', (code) => {
        console.log(`script exited with code ${code}`);
    });
}

function pleaseWaitAnimation(){
    var button = document.getElementById('Result');
    button.innerHTML = 'Please Wait.<span aria-hidden>_</span><span aria-hidden class="cybr-btn__glitch">Completed_</span><span aria-hidden class="cybr-btn__tag">R26</span>';
    button.style.backgroundColor = 'white';
}

function loading(counter){
    var button = document.getElementById('Result');
    button.innerHTML = `${counter}/6<span aria-hidden>_</span><span aria-hidden class="cybr-btn__glitch">Completed_</span><span aria-hidden class="cybr-btn__tag">R26</span>`;
    button.style.backgroundColor = 'white';
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

document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('autoReservationBtn');
    if (button) {
      button.addEventListener('click', autoReservation);
    }
  });

  document.addEventListener('DOMContentLoaded', () => {
    const decrementBtn = document.getElementById('decrementBtn');
    const incrementBtn = document.getElementById('incrementBtn');
    const counterValue = document.getElementById('counterValue');
  
    // Get the current date number
    const initialDate = new Date().getDate();
    currentDate = initialDate;
  
    // Function to update the display
    function updateDisplay() {
      counterValue.textContent = currentDate;
      // Update the disabled state of the decrement button
      if (currentDate <= initialDate) {
        decrementBtn.classList.add('disabled');
      } else {
        decrementBtn.classList.remove('disabled');
      }
    }
  
    // Initial display
    updateDisplay();
  
    decrementBtn.addEventListener('click', () => {
      if (currentDate > initialDate) {
        currentDate -= 1;
        updateDisplay();
      }
    });
  
    incrementBtn.addEventListener('click', () => {
      currentDate += 1;
      updateDisplay();
    });
  });
  
