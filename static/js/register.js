$(document).ready(function(){
    function update_btn(){
        if($('#nickname').val().length > 0 && $('#gender').val() != '' && $('#pwd').val().length > 0 && $('#pwd2').val().length > 0){
            $('#register').removeClass('disabled');
        }else{
            $('#register').addClass('disabled');
        }
        $("#tips").hide();
    }

    $('#pwd').on('click', function(){
       update_btn()
    });

    $('#pwd2').on('click', function(){
       update_btn()
    });

    //selct sex
    $('.btn').on('click',function(){
        var _this = $(this);
        _this.addClass('act').siblings().removeClass('act');
        $('#gender').val(_this.attr('value'));
        update_btn()
    });

    //click register
    $('.register').on('click',function(){
        pwd = $('#pwd').val()
        pwd2 = $('#pwd2').val()
        if($('#nickname').val().length > 0 && pwd.length > 0 && pwd2.length > 0 && $('#gender').val() != ''){
            if(pwd == pwd2){
                $('form').submit()
            }else{
                $('#tips').show();
                document.getElementById("tips").innerHTML = "两次输入的密码不一致，请重新输入";
            }
        }
    });

    $('#nickname').on('keyup', function(e){
        update_btn()
    })
});
