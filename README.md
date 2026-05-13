# bin_collections_sheffield
Home assistant addon for bin collection data in sheffield.

This custom component was written after the UK Bin Collection Data https://github.com/robbrad/UKBinCollectionData/wiki stopped working after the Sheffield council website was updated.

Thanks to Tom Whiteley https://github.com/Tom-Whi for finding the APi endpoint which was still working.

Thanks to https://github.com/i3lade4life for making me aware of the UPRN website.


To Use follow the steps below:

1. Go to https://uprn.uk/ and enter your postcode, select your address and copy the UPRN number provided.

2. Install this repo as a custom repository in HACS using https://github.com/st3nic/bin_collections_sheffield

3. Search for Sheffield bins and download from HACS

4. Home Assiatant will want a restart, afterwards go to settings > Devices & services > click Add Integration and search for sheffield bins.

5. Enter you UPRN which you copied in step one.

6. Add the sensors to your dashboard.


Warning!! We have no idea if the API will be switched off now the council has a new website, fingers crossed its left operational.
