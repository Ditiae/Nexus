<?php

header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");

function e($msg, $code=400) {
  http_response_code($code);
  echo json_encode(array("status" => "error", "message" => $msg));
  die();
}

require("../../../settings.inc");

$conn = mysqli_connect($DB_SERVER, $DB_USER, $DB_PASSWORD, $DB_NAME);

if (!$conn) { // if that connection didn't work
    e("Internal server error", $code=500);
}

if (empty($_POST["key"])) {
  e("Provide an auth key");
} elseif (!in_array($_POST["key"], $AUTH_KEYS)) {
  e("Invalid auth key", $code=403);
}

$fields = array("mod_id", "mod_name", "mod_desc", "file_id", "size_kb", "category_name", "content_preview", "external_virus_scan_url");
$inputs = array();

$valstring = "";
$markstring = "";
foreach ($fields as $name) {
  $valstring .= "{$name},";
  $markstring .= "?,";
}
$valstring = substr($valstring, 0, -1);
$markstring = substr($markstring, 0, -1);

// check none null fields
$cannot_be_empty = ["mod_id", "mod_name", "file_id", "size_kb"];
foreach ($cannot_be_empty as $name) {
  if (empty($_POST[$name])) {
    e("Failed - specify param {$name} in POST");
  }
}

// assign values to fields
foreach ($fields as $name) {
  if (empty($_POST[$name])) {
    $inputs[$name] = NULL;
  } else {
    $inputs[$name] = $_POST[$name];
  }
}

// check integers
$fields_with_integers = ["file_id", "size_kb"];
foreach ($fields_with_integers as $name) {
  if ((!ctype_digit($inputs[$name])) || (strpos($inputs[$name], ".") !== false)) {
    e("{$name} can only be an integer");
  }
}

// check number - can have a decimal point
if ((!ctype_digit(str_replace(".", "", $inputs["mod_id"])))) {
  e("mod_id can only be numbers");
}

// check json validity
json_decode($inputs["content_preview"]);
if (json_last_error() != JSON_ERROR_NONE) {
  e("content_preview is not valid JSON");
}

$sqlstr = "INSERT INTO skyrim ({$valstring}) VALUES ({$markstring})";

$sql = $conn->prepare($sqlstr);
$fields = array("mod_id", "mod_name", "mod_desc", "file_id", "size_kb", "category_name", "content_preview", "external_virus_scan_url");
$sql->bind_param("ssssssss", $inputs["mod_id"], $inputs["mod_name"], $inputs["mod_desc"], $inputs["file_id"], $inputs["size_kb"], $inputs["category_name"], $inputs["content_preview"], $inputs["external_virus_scan_url"]);

$sql->execute();
$sql->close();


echo json_encode(array("status" => "ok", "message" => "Success!"));
