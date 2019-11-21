<?php

require("../../../common.php");

$cannot_be_empty = ["mod_id"];
foreach ($cannot_be_empty as $name) {
    if (!array_key_exists($name, $_POST)) {
        e("Failed - specify param {$name} in POST");
    }
}

// check number - can have a decimal point
if ((!ctype_digit(str_replace(".", "", $_POST["mod_id"])))) {
  e("mod_id can only be numbers (with a decimal point if required)");
}

// make SQL query
$sql = $conn->prepare("SELECT *FROM skyrim WHERE mod_id = ?");
$sql->bind_param("s", $_POST["mod_id"]);
$sql->execute();

$result = $sql->get_result();

if ($result->num_rows > 0) {
	$row = $result->fetch_assoc();
    echo json_encode(array("status" => "ok", "message" => "Success!", "content" => $row));
} else {
    http_response_code(404);
    echo json_encode(array("status" => "error", "message" => "No rows exist in database", "content" => null));
}
