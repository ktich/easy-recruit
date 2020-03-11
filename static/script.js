//to learn how to do this, used and adapted code from: https://www.w3schools.com/jsref/prop_checkbox_required.asp

function checkboxrequired() {
  var x = document.getElementById("reviewcheck").required;
  document.getElementById("prompt").innerHTML = x;
}

function requiredfield() {
  var x = document.getElementById("emptyfield").required;
  document.getElementById("prompt").innerHTML = x;
}


