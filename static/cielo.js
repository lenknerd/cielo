/* Event handing for Cielo app.
 *
 * 1. Call new game API when new game button clicked,
 * 2. Update the state (high score, feed, summary) on load and
 *    timer and also after new game initiated
 */


$(".cielonewgame").click(function() {
  $.ajax({
    url: "/newgame",
    success: function(response) {
      update_state();
    }
  });
})


function update_state() {
  $.ajax({
    url: "/state",
    success: function(data) {
      $(".cielofeed").html(data.feed);
      $(".cielogamesummary").html(data.summary);
      $(".cielohighscore").html(data.highscore);
    }
  });
}


$(window).on('load', update_state);

setInterval(update_state, 3000);
