$(document).ready(function () {
  function update_btn() {
    if ($("#nickname").val().length > 0 && $("#gender").val() != "") {
      $("#register").removeClass("disabled");
    } else {
      $("#register").addClass("disabled");
    }
    $("#tips").hide();
  }

  //selct sex
  $(".btn").on("click", function () {
    var _this = $(this);
    _this.addClass("act").siblings().removeClass("act");
    $("#gender").val(_this.attr("value"));
    update_btn();
  });

  //click register
  $(".register").on("click", function () {
    if ($("#nickname").val().length > 0 && $("#gender").val() != "") {
      $("form").submit();
    }
  });

  $("#nickname").on("keyup", function (e) {
    update_btn();
  });
});
