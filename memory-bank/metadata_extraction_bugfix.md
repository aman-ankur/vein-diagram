# PDF Metadata Extraction Bugfix

## Issue

When trying to upload a PDF file and match it to a profile, the following error was occurring:

```
Error matching profile: 'PDF' object has no attribute 'replace'
```

This happened during the call to `extract_metadata_with_claude` from the profile matching endpoint.

## Root Cause Analysis

1. In `backend/app/services/metadata_parser.py`, the function is defined as:
   ```python
   def extract_metadata_with_claude(text: str, filename: str) -> Dict[str, Any]:
   ```
   
   It expects a string text input and a filename string.

2. However, in `backend/app/api/routes/profile_routes.py`, it was being called with:
   ```python
   metadata = await extract_metadata_with_claude(pdf, db)
   ```
   
   The function was receiving a PDF object and a database session, causing a type error when the function tried to call `replace()` on what it expected to be a string.

## Fix

1. Added type checking at the beginning of the `extract_metadata_with_claude` function:
   ```python
   if not isinstance(text, str):
       logger.error(f"[TYPE_ERROR] extract_metadata_with_claude expected text as string, got {type(text)}")
       return {}
       
   if not text:
       logger.warning(f"[EMPTY_TEXT] extract_metadata_with_claude received empty text for {filename}")
       return {}
   ```

2. Fixed the calls in `profile_routes.py` to properly extract the text from the PDF object:
   ```python
   if not pdf.extracted_text:
       logger.error(f"PDF {request.pdf_id} doesn't have extracted text. Status: {pdf.status}")
       raise HTTPException(
           status_code=400, 
           detail=f"PDF text has not been extracted yet. Current status: {pdf.status}"
       )
       
   metadata = await extract_metadata_with_claude(pdf.extracted_text, pdf.filename)
   ```

3. Added better error messages that include the PDF's current processing status to help with debugging.

## Lessons Learned

1. **Type Checking**: Always include type checking for critical functions, especially when dealing with API integrations.
2. **Error Handling**: Provide detailed error messages that include relevant state information to aid in debugging.
3. **Function Documentation**: Make sure that the function documentation clearly indicates expected parameter types.
4. **Code Review**: This type of error should be caught during code review, as the parameter types were clearly mismatched.

## Related Files

- `backend/app/services/metadata_parser.py` - Contains the implementation of `extract_metadata_with_claude`
- `backend/app/api/routes/profile_routes.py` - Contains the profile matching endpoint that calls the function 