if (window.innerWidth < 768) {
	$('[data-bss-disabled-mobile]').removeClass('animated').removeAttr('data-aos data-bss-hover-animate data-bss-parallax-bg data-bss-scroll-zoom');
}

$(document).ready(function(){
	if ('AOS' in window) {
		AOS.init();
	}
	
    // Initializing the swiper plugin for the slider.
    // Read more here: http://idangero.us/swiper/api/
    // mySwiper
    var mySwiper = new Swiper ('.swiper-container', {
        loop: true,
        DelayNode: 100,

        pagination: '.swiper-pagination',
        paginationClickable: true,
        nextButton: '.swiper-button-next',
        prevButton: '.swiper-button-prev'
    });
});

