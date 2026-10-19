# Publish the MF Intelligence Showcase

## Before uploading
- This package uses fictional example holdings and a synthetic NAV sample.
- It does not need API keys or secrets for the current demo.
- Do not add personal statements, PAN, folio numbers, bank details, passwords, or private data.
- If using a public GitHub repository, anyone can view the source code and included files.

## Publish through GitHub's website
1. Sign in to GitHub and choose **New repository**.
2. Name it `mf-intelligence-showcase`.
3. For the easiest family demo, choose **Public** only after confirming the package contains no confidential data. A public repo exposes its code; it is not required to share a public Streamlit app if your deployment settings support a private app.
4. Create the repository. Do not initialize it with a README if you will upload all files from this ZIP (optional: if you do initialize it, GitHub may require resolving the existing README before upload).
5. Extract this ZIP on your computer. On the new repository page, choose **Add file → Upload files**.
6. Upload the *contents* of the extracted folder—not the enclosing folder—so `app.py` and `requirements.txt` are at the repository root. Include `.streamlit/config.toml` and `data/sample_nav_synthetic.csv`.
7. Commit the files to the `main` branch.

## Deploy through Streamlit Community Cloud
1. Open https://share.streamlit.io/ and sign in with GitHub.
2. Authorize Streamlit to access the repository when prompted.
3. Select **Create app**.
4. Select repository `mf-intelligence-showcase`, branch `main`, and main file path `app.py`.
5. Optionally choose an available custom app URL, then click **Deploy**.
6. Wait for the deployment to finish. If it fails, open the app's logs and address the first error shown.
7. When it loads, test add/edit/delete holding, CSV import/export, NAV sample analysis, and mobile layout.
8. Open the published URL in a private/incognito browser window and on a phone before sharing it.

## Limitations
This is a prototype, not a live investment service. The sample NAV is synthetic; 60/40 scores are manually entered; no database, automatic live NAV refresh, verified tax engine, news engine, or personalised financial recommendation is implemented. Inputs are temporary and should not be treated as saved between sessions.
