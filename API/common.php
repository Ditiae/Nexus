<?php
// Set required application headers
header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");


// Function to throw an error
function e($msg, $code=400) {
  http_response_code($code);
  echo json_encode(array("status" => "error", "message" => $msg));
  die();
}


if($_SERVER['REQUEST_METHOD'] != "POST") {
  header("Allow: POST");
  e("Only POST requests allowed", $code=405);
}

require("settings.inc");

mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
$conn = mysqli_connect($DB_SERVER, $DB_USER, $DB_PASSWORD, $DB_NAME);

if (!$conn) { // if that connection didn't work
    e("Internal server error", $code=500);
}

// check authentication key
if (!array_key_exists("key", $_POST)) {
  e("Provide an auth key");
} elseif (!in_array($_POST["key"], $AUTH_KEYS)) {  // check auth key
  e("Invalid auth key", $code=403);
}
