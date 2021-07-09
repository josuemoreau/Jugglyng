(function() {
    'use strict';
    
    var sound42 = new Howl({
        src: ['../../do.wav']
    });

    alert("hello");

    sound42.play();
})()