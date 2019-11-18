<?php

require("../../../common.php");

$fields = array("mod_id", "mod_name", "mod_desc", "mod_version", "file_id", "size_kb", "category_name", "adult_content", "content_preview", "uploaded_time", "external_virus_scan_url");
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
$cannot_be_empty = ["mod_id", "mod_name"];
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

// check integers
$fields_with_integers = ["file_id", "size_kb", "uploaded_time"];
foreach ($fields_with_integers as $name) {
  if ($inputs[$name] != NULL) {
    if ((!is_numeric($inputs[$name])) || (strpos($inputs[$name], ".") !== false)) {
      e("{$name} can only be an integer");
    }
  }
}

// check booleans
$fields_with_booleans = ["adult_content"];
foreach ($fields_with_booleans as $name) {
  if (!(($inputs[$name] === NULL) || (in_array($inputs[$name], array("1", "0"))))) {
    e("{$name} can only only accept one of the following: 1, 0, true, false or null");  // true/false filtered out when loading POST params
  }
}

// check number - can have a decimal point
if ((!ctype_digit(str_replace(".", "", $inputs["mod_id"])))) {
  e("mod_id can only be numbers (with a decimal point if required)");
}

// check json validity
json_decode($inputs["content_preview"]);
if (json_last_error() != JSON_ERROR_NONE) {
  e("content_preview is not valid JSON");
}

$sqlstr = "REPLACE INTO skyrim ({$valstring}) VALUES ({$markstring})";

$sql = $conn->prepare($sqlstr);

if (!$sql) {
  e("Internal server error", $code=500);
}

$sql->bind_param("sssssssssss", $inputs["mod_id"], $inputs["mod_name"], $inputs["mod_desc"], $inputs["mod_version"], $inputs["file_id"], $inputs["size_kb"], $inputs["category_name"], $inputs["adult_content"], $inputs["content_preview"], $inputs["uploaded_time"], $inputs["external_virus_scan_url"]);

$sql->execute();
$sql->close();

http_response_code(201);
echo json_encode(array("status" => "ok", "message" => "Success!"));
