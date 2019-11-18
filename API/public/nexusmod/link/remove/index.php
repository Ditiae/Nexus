<?php

require("../../../../common.php");

// check mod_id specified
if (!array_key_exists("mod_id", $_POST)) {
  e("Failed - specify param mod_id in POST");
}

// validate mod_id
if ((!ctype_digit(str_replace(".", "", $_POST["mod_id"])))) {
  e("mod_id can only be numbers (with a decimal point if required)");
}

// check mod_id has an entry

$sql = $conn->prepare("SELECT * FROM skyrim_downloads WHERE mod_id = ?");

$sql->bind_param("s", $_POST["mod_id"]);
$sql->execute();

$result = $sql->get_result();

$sql->close;

if ($result->num_rows == 0) {
  e("No entry exists with specified ID");
}


// make request
$sql = $conn->prepare("DELETE FROM skyrim_downloads WHERE mod_id = ? LIMIT 1");

$sql->bind_param("s", $_POST["mod_id"]);
$sql->execute();

$sql->close();

echo json_encode(array("status" => "ok", "message" => "Success!"));
