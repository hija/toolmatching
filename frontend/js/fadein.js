$('.element-to-hide').css('visibility', 'hidden');

$(window).scroll(function() {

    $('.animation-fade').each(function(){

        var imagePos = $(this).offset().top;
        var topOfWindow = $(window).scrollTop();
        var screenw = document.documentElement.clientWidth;
        var screenh = document.documentElement.clientHeight;
        var topOfW = 600;

        if (screenw<400) {
            topOfW = 900;
        } else {
            topOfW = 500;
        }

        if (imagePos < topOfWindow + topOfW) {
            $(this).addClass("animated");
            $(this).addClass("animatedFadeInUp");
            $(this).addClass("fadeInUp");
        }




    });

});
