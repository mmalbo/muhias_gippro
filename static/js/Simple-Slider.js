$(function(){

    // Initializing the swiper plugin for the slider.
    // Read more here: http://idangero.us/swiper/api/
    // mySwiper
    var swiper = new Swiper ('.slider1', {
        slidesPerView: 2,
        spaceBetween: 4,
        lazyLoading: true,
        DelayNode: 100,
        direction: 'horizontal',

        pagination: '.swiper-pagination',
        paginationClickable: true,
        nextButton: '.swiper-button-next',
        prevButton: '.swiper-button-prev'
    });
    
});