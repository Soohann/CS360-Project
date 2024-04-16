<?php
// Enable error reporting and display errors
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Check if a file is uploaded
if ($_FILES["pdf_file"]["error"] == UPLOAD_ERR_OK && $_FILES["pdf_file"]["size"] > 0) {
    // Connect to the database (replace with your database credentials)
    $conn = new mysqli("localhost", "username", "password", "database_name");

    // Check connection
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    // Prepare the SQL statement
    $stmt = $conn->prepare("INSERT INTO pdf_files (file_name, file_data) VALUES (?, ?)");
    $stmt->bind_param("sb", $file_name, $file_data);

    // Get file data
    $file_name = $_FILES["pdf_file"]["name"];
    $file_data = file_get_contents($_FILES["pdf_file"]["tmp_name"]);

    // Execute the statement
    if ($stmt->execute()) {
        echo "File uploaded successfully.";
    } else {
        echo "Error uploading file: " . $stmt->error;
    }

    // Close connections
    $stmt->close();
    $conn->close();
} else {
    echo "Error uploading file.";
}
?>
