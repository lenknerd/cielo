/* Event handing for Cielo app.
 *
 * Three basic things happen;
 *  - Update the status feed and game headline on a timer
 *  - On new game click, tell server new game via API call
 *  - On page load or new game click, update high score box
 */

function update_high_score() {
  $.ajax({
    url: "/highscore",
    success: function(response) {
      $(".cielohighscore").html(response);
    }
  });
}

$(".cielonewgame").click(function() {
  $.ajax({
    url: "/newgame",
    success: function(response) {
      update_status_and_feed();
      update_high_score();
    }
  });
})

function update_status_and_feed() {
  $.ajax({
    url: "/feed",
    success: function(response) {
      $(".cielofeed").html(response);
    }
  });

  $.ajax({
    url: "/summary",
    success: function(response) {
      $(".cielogamesummary").html(response);
    }
  });
}

setInterval(update_status_and_feed, 3000);
