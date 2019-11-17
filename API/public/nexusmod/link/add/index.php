<?php

require("../../../../common.inc");

$fields = array("mod_id", "download_url");
$inputs = array();

// valstring and markstring used for SQL query to populate with values
$valstring = "";
$markstring = "";
foreach ($fields as $name) {
  $valstring .= "{$name},";
  $markstring .= "?,";
}
$valstring = substr($valstring, 0, -1);  // remove extra comma from each
$markstring = substr($markstring, 0, -1);

// check required fields
$cannot_be_empty = ["mod_id", "download_url"];
foreach ($cannot_be_empty as $name) {
  if (!array_key_exists($name, $_POST)) {
    e("Failed - specify param {$name} in POST");
  }
}

// assign values to fields
foreach ($fields as $name) {
  if ((!array_key_exists($name, $_POST)) || (strtolower($_POST[$name]) == "null")) {
    $inputs[$name] = NULL;
  } elseif (strtolower($_POST[$name]) == "true") {
    $inputs[$name] = "1";
  } elseif (strtolower($_POST[$name]) == "false") {
    $inputs[$name] = "0";
  } else {
    $inputs[$name] = $_POST[$name];
  }
}

// check number - can have a decimal point
if ((!ctype_digit(str_replace(".", "", $inputs["mod_id"])))) {
  e("mod_id can only be numbers (with a decimal point if required)");
}

// make request
$sqlstr = "INSERT INTO skyrim_downloads ({$valstring}) VALUES ({$markstring})";

$sql = $conn->prepare($sqlstr);

if (!$sql) {
  e("Internal server error", $code=500);
}

$sql->bind_param("ss", $inputs["mod_id"], $inputs["download_url"]);

$sql->execute();
$sql->close();

echo json_encode(array("status" => "ok", "message" => "Success!"));
