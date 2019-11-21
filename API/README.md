# Internal API

### Endpoints

#### Create mod entry

Endpoint - https://arch.tdpain.net/api/nexusmod/create/

Method - POST

Returns - HTTP 201 on success

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
- `key` - **required**. Internal API authentication key.

#### Update a mod entry

*If the mod ID exists and `category_name` for that mod is set to one of the following, the row will be updated with the values provided. Otherwise, it will fail.*
- `NOT FOUND`
- `HIDDEN MOD`
- `NO FILES`
- `NOT PUBLISHED`
- `UNDER MODERATION`
- `NON`

Endpoint - https://arch.tdpain.net/api/nexusmod/update/

Method - POST

Returns - HTTP 200 on success, HTTP 404 if row not found, HTTP 400 if `category_name` is invalid

Parameters:

- `mod_id` - **required** and can be a number with a decimal point
- `mod_name`
- `mod_desc`
- `mod_version`
- `file_id` - must be integer if specified in request
- `size_kb` - must be integer if specified in request
- `category_name`
- `adult_content` - must be Boolean if specified in request
- `content_preview` - must be valid JSON if specified in request
- `external_virus_scan_url`
- `uploaded_time` - must be an integer timestamp if specified in request
- `key` - **required**. Internal API authentication key.

#### Retrieve a mod entry

Endpoint - https://arch.tdpain.net/api/nexusmod/select/

Method - POST

Returns - HTTP 200 on success, HTTP 404 if ID not found

Parameters:

- `mod_id` - **required** and can be a number with a decimal point
- `key` - **required**. Internal API authentication key.


#### Add download link to mod entry

Endpoint - https://arch.tdpain.net/api/nexusmod/link/add/

Method - POST

Returns - HTTP 201 on success

Parameters:

- `mod_id` - **required** and can be a number with a decimal point. Value specified must already have been created using the create mod entry endpoint, otherwise "Invalid mod_id" will be returned from the API.
- `download_url` - **required**.
- `key` - **required**. Internal API authentication key.

#### Remove a download link from a mod entry

Endpoint - https://arch.tdpain.net/api/nexusmod/link/remove/

Method - POST

Returns: HTTP 200 on success, HTTP 404 if `mod_id` not found

Parameters:

- `mod_id` - **required** and can be a number with a decimal point. Value specified must already have been created using the add link entry endpoint, otherwise "No entry exists with specified ID" will be returned from the API, along with a HTTP 400 error.
- `key` - **required**. Internal API authentication key.

#### Retrieve a download link for a mod entry

Endpoint - https://arch.tdpain.net/api/nexusmod/link/select/

Method - POST

Returns - HTTP 200 on success, HTTP 404 if no entries exist

Parameters:
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
