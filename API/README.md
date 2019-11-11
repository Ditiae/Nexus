# Upload API

Endpoint - https://arch.tdpain.net/api/nexusmod/create/

Params

 * `mod_id` (required and must be int)
 * `mod_name` (required)
 * `mod_desc`
 * `mod_version`
 * `file_id` (required and must be int)
 * `size_kb` (required and must be int)
 * `category_name`
 * `content_preview` (must be valid JSON)
 * `external_virus_scan_url`
 * `key` (Authentication key, required)

Only POST requests are accepted.
