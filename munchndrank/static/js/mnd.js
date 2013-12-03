var saveRecipe = function(evt) {
  var food_list = new Array();
  var rows = $('.reciperow');
  rows.each(function(row){
    var food_item = {};
    food_item.name = $(rows[row]).find('.foodfield').val();
    food_item.qty = $(rows[row]).find('.qtyfield').val();
    food_item.metrics = $(rows[row]).find('.metricfield').val();
    food_list.push(food_item);
  });
  
  var token = $('input[name="csrfmiddlewaretoken"]').prop('value');
  var drink_flag = 0;
  if ($('#isDrink').is(':checked')) {
    drink_flag = 1;   
  } else {
    drink_flag = 0;
  }

  var serves = 1;
  if ($('#servefield').val()) {
    serves = parseInt($('#servefield').val());
  }

  $.ajax({
    url: 'post-recipe',
    type: 'POST',
    data: {
      'recipe':  JSON.stringify({'food_list': food_list}),
      'recipe_name': $('#recipe_name').val(),
      'drink_flag': drink_flag,
      'instructions': $('#instrfield').val(),
      'serves_num': serves,
      'csrfmiddlewaretoken': token
    },
    success: function(data){
      if (data.success && data.success == 1){
        console.log('Save recipe success');
        window.location.replace("/munchndrank/recipe-photo")
      } else if (data.error && data.error == 1){
        console.log('Save recipe failed');
      }
    }
  });
}

var saveEdit = function(evt) {
  var food_list = new Array();
  var rows = $('.reciperow');
  rows.each(function(row){
    var food_item = {};
    food_item.name = $(rows[row]).find('.foodfield').val();
    food_item.qty = $(rows[row]).find('.qtyfield').val();
    food_item.metrics = $(rows[row]).find('.metricfield').val();
    food_list.push(food_item);
  });
  
  var token = $('input[name="csrfmiddlewaretoken"]').prop('value');

  var serves = 1;
  if ($('#servefield').val()) {
    serves = parseInt($('#servefield').val());
  }

  $.ajax({
    url: '/munchndrank/save-edit',
    type: 'POST',
    data: {
      'recipe':  JSON.stringify({'food_list': food_list}),
      'recipe_name': $('#recipe_name').val(),
      'recipe_id': $('#recipeid').val(),
      'instructions': $('#instrfield').val(),
      'serves_num': serves,
      'csrfmiddlewaretoken': token,
    },
    success: function(data){
      if (data.success && data.success == 1){
        console.log('Save recipe success');
        window.location.replace("/munchndrank/recipe/" + parseInt($('#recipeid').val()))
      } else if (data.error && data.error == 1){
        console.log('Save recipe failed');
      }
    }
  });
}

var nearFoodHandler = function(request, response) {
  var text = request.term;
  var matcher = new RegExp( $.ui.autocomplete.escapeRegex(text), "i");
  var token = $('input[name="csrfmiddlewaretoken"]').prop('value');
    $.ajax({
      url: 'nearest-food',
      type: 'POST',
      data: {
        'text': text,
        'csrfmiddlewaretoken': token
      },
      success: function(data) {
        if (data.success && data.success == 1){
          console.log('food suggestion success');
          console.log(data.food_suggestions);
          response($.map(data.food_suggestions, function(v,i){
            var item  = v.name;
            if (item && (!text || matcher.test(item))){
              return {
                label: v.name,
                value: v.name
              };
            }
          }));

        } else if (data.error && data.error == 1){
          console.log('food suggestion failed');
        }
      },
      error: function() {
        console.log('FAILED');
      }
  });
// if text  }
}

var followStreamHandler = function(evt){
  var button = $(evt.target);
  var token = $('input[name="csrfmiddlewaretoken"]').prop('value');
  var is_followed = button.parent().find('input.is_followed').prop('value');
  var user_id = button.parent().find('input.user_id').prop('value'); 
  $.ajax({
    url: 'followstream',
    type: 'POST',
    data: {
      'user_id': user_id,
      'is_followed': is_followed,
      'csrfmiddlewaretoken': token
    },
    success: function(data) {
      if (data.success && data.success == 1){
        console.log('follow/unfollow success');
        var div = $('#stream-' + data.user_id + "-div");
        var btn = div.children('.follow-stream-btn');
        var hidden_input = div.find('.is_followed');
        if (data.is_followed == 0) {
          btn.html("Follow");
          hidden_input.val(0);
        } else if (data.is_followed == 1) {
          btn.html("Unfollow");
          hidden_input.val(1);
        }
      } else if (data.error && data.error == 1){
        console.log('follow/unfollow error');
        console.log(data.errors);
      }
    }
  });
}

var searchStreamHandler = function(evt){
  var text = $('#searchStreamTextField').val();
  var token = $('input[name="csrfmiddlewaretoken"]').prop('value');
 
  $.ajax({
    url: 'searchstream',
    type: 'POST',
    data: {
      'search_term': text,
      'csrfmiddlewaretoken': token
    },
    success: function(data){
      if (data.success && data.success == 1) {
        console.log('searchstream success');
        var div = $('#search_results_div');
        div.empty();
        div.append(data.text); 
        $('.follow-stream-btn').unbind('click').click(followStreamHandler);
      } else if (data.error && data.error == 1){
        console.log('searchstream fail');
        console.log(data.errors);
      }
    }
  });
}

var ratingHandler = function(evt){
  var ri = $(this);
  var value = ri.rateit('value');
  var recipe_id = ri.data('recipeid');
  var token = $('input[name="csrfmiddlewaretoken"]').prop('value');

  $.ajax({
    url: '/munchndrank/update-rating',
    type: 'POST',
    data: {
      'recipe_id': recipe_id,
      'value': value,
      'csrfmiddlewaretoken':token
    },
    success: function(data){
      if (data.success && data.success == 1) {
        console.log('rating success');
      } else if (data.error && data.error == 1){
        console.log('rating error');
        console.log(errors);
      }
    }
  });
  
}

$(document).ready(function() {
  //change serving sizes
  $('#changeservings').click( function() {
    var serving_size = $('#nserv').val();
    var target_size = $('#servings').val();
    var new_val;
    $('.ing_val').each(function() {
      var original_val = $(this).text();
      new_val = original_val * ((target_size * 1)/ (serving_size * 1));
      $(this).text(new_val);
      //$('#nserv').val(new_val);
    });
  });
  

  // give autocomplete suggestions for food fields
  $('.foodfield').each(function(i, el) {
    el = $(el);
    el.autocomplete({
    source: nearFoodHandler,
    minlength: 1,
    open: function() {
        $( this ).removeClass( "ui-corner-all" ).addClass( "ui-corner-top" );
      },
    close: function() {
        $( this ).removeClass( "ui-corner-top" ).addClass( "ui-corner-all" );
      }   
    });
  });

  $("#Add").click(function() {
    $("#t_ingredient tbody:first").append(
    '<tr class=\"reciperow\">' + 
    '<td><input type=\"text\" placeholder=\"Quantity e.g. 2\" class=\"form-control qtyfield\"></td>' +
    '<td><input type=\"text\" placeholder=\"Units e.g. pounds\" class=\"form-control metricfield\"></td>' +
    '<td><input type=\"text\" placeholder=\"e.g. Chicken\" class=\"form-control foodfield\"></td></tr>');
    $("#s_ingredient tbody:first").append(
    '<tr class=\"reciperow\">' + 
    '<td><input type=\"text\" placeholder=\"e.g. Chicken\" class=\"form-control\" name=\"foodfield\"></td></tr>');
    $('.foodfield').unbind('keyup').keyup(nearFoodHandler);
    return false;
  });

  $('#editRecipeBtn').click(saveEdit);
  $('#postRecipeBtn').click(saveRecipe);
  $('.follow-stream-btn').click(followStreamHandler);
  $('#searchStreamBtn').click(searchStreamHandler);
  $('.rateit').bind('rated rest',ratingHandler);
});
