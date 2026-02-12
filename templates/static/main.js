const pupils = document.querySelectorAll('.pupil');
const chars = document.querySelectorAll('.char');
const eyesL = document.querySelectorAll('.e1');
const passField = document.getElementById('pass-field');
const userField = document.getElementById('user-field');

let mouseX = innerWidth/2;
let mouseY = innerHeight/2;

document.addEventListener('mousemove', e=>{
    mouseX = e.clientX;
    mouseY = e.clientY;
});

function loop(){

    pupils.forEach(p=>{
        const r = p.getBoundingClientRect();
        const cx = r.left+r.width/2;
        const cy = r.top+r.height/2;

        const dx = mouseX-cx;
        const dy = mouseY-cy;

        const angle = Math.atan2(dy,dx);
        const dist = Math.min(6, Math.hypot(dx,dy)/12);

        p.style.transform=`translate(${Math.cos(angle)*dist}px,${Math.sin(angle)*dist}px);`
    });

    chars.forEach((c,i)=>{
        const x=(mouseX-innerWidth/2)/(28+i*6);
        const y=(mouseY-innerHeight/2)/(28+i*6);
        c.style.transform=`translate(${x}px,${y}px) rotate(${x*0.5}deg);`
    });

    requestAnimationFrame(loop);
}

loop();

passField.addEventListener("focus",()=>{
    eyesL.forEach(e=>e.style.height="3px");
});
passField.addEventListener("blur",()=>{
    eyesL.forEach(e=>e.style.height="14px");
});

[userField,passField].forEach(f=>{
    f.addEventListener("focus",()=>{
        chars.forEach(c=>{
            c.animate([{transform:c.style.transform},
                       {transform:c.style.transform+" translateY(-10px)"},
                       {transform:c.style.transform}],{duration:250});
        });
    });
});