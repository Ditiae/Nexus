<?php

require("../../../../common.php");

// make SQL query
$sql = $conn->prepare("SELECT skyrim_downloads.*, skyrim.mod_name, skyrim.mod_version FROM skyrim_downloads JOIN skyrim ON skyrim.mod_id = skyrim_downloads.mod_id LIMIT 1");
$sql->execute();
$result = $sql->get_result();

if ($result->num_rows > 0) {
	$row = $result->fetch_assoc();
  echo json_encode(array("status" => "ok", "message" => "Success!", "content" => $row));
} else {
  http_response_code(404);
  echo json_encode(array("status" => "error", "message" => "No rows exist in database", "content" => null));
}
