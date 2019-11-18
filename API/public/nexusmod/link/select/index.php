<?php

require("../../../../common.php");

// make SQL query
$sql = $conn->prepare("SELECT * FROM skyrim_downloads LIMIT 1");
$sql->execute();
$result = $sql->get_result();

if ($results->num_rows > 0) {
	$row = $results->fetch_assoc();
	echo json_encode($row, JSON_FORCE_OBJECT);
} else {
	echo "Nothing was returned :(";
}
