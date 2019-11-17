# Internal API

### Endpoints

#### Create mod entry

Endpoint - https://arch.tdpain.net/api/nexusmod/create/

Method - POST

Parameters:

- `mod_id` - **required** and can be a number with a decimal point
- `mod_name` - **required**.
- `mod_desc`
- `mod_version`
- `file_id` - must be integer if specified in request
- `size_kb` - must be integer if specified in request
- `category_name`
- `adult_content` - must be Boolean if specified in request
- `content_preview` - must be valid JSON if specified in request
- `external_virus_scan_url`
- `uploaded_time` - must be an integer timestamp if specified in request
- `key` - Authentication key, required

#### Add download link to mod entry

Endpoint - https://arch.tdpain.net/api/nexusmod/link/add/

Method - POST

Parameters:

- `mod_id` - **required** and can be a number with a decimal point. Value specified must already have been created using the create mod entry endpoint, otherwise "Invalid mod_id" will be returned from the API.
- `download_url` - **required**. 
- `key` - **required**. Internal API authentication key.



### Specifying a parameter as NULL

If a parameter should be NULL, it can be one of the following:

- not specified in the request
- "null" in any capitalisation

### Specifying a parameter as a Boolean

If a parameter should be a Boolean, it can be one of the following:

- "1"
- "0"
- "true" in any capitalisation
- "false" in any capitalisation
