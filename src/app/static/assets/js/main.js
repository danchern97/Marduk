$(document).ready(function() {

	$('html').on('click', '.projects-new-btn', function(e) {
    	$(this).css('display', 'none');
    	$('.projects-new-form').css('display', 'block');
 	});

	$( ".header-ham" ).click(function() {
	    event.preventDefault();
	    var offset = $(this).offset();
	    var menuTop = offset.top + 40;
	    var menuLeft = offset.left - 20;
    	$("#context-menu-header").finish().toggle(50).
    	css({
        	top: menuTop + "px",
        	left: menuLeft + "px"
    	});
	});
	$(document).bind("mousedown", function (e) {
	    if (!$(e.target).parents(".custom-menu").length > 0) {
	        $("#context-menu-header").hide(50);
	    }
	});

});
