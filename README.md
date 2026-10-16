# bin_collections_sheffield
Home Assistant integration for bin collection data in Sheffield.

This custom component was written after the UK Bin Collection Data https://github.com/robbrad/UKBinCollectionData/wiki stopped working after the Sheffield council website was updated.

Thanks to Tom Whiteley https://github.com/Tom-Whi for finding the API endpoint which was still working.

Thanks to https://github.com/i3lade4life for making me aware of the UPRN website.


To use, follow the steps below:

1. Go to https://uprn.uk/ and enter your postcode, select your address and copy the UPRN number provided.

2. Install this repo as a custom repository in HACS using https://github.com/st3nic/bin_collections_sheffield

3. Search for Sheffield bins and download from HACS

4. Home Assistant will want a restart, afterwards go to Settings > Devices & services > click Add Integration and search for Sheffield bins.

5. Enter your UPRN which you copied in step one.

6. Add the sensors to your dashboard.


## What you get

Each bin the council collects from your address gets its own device with three sensors. Only bins that appear in the council's data are added, so you won't get a Green Bin unless you have one.

| Sensor | Example | Use it for |
|---|---|---|
| `sensor.black_bin_collection` | `Today`, `Tomorrow`, `In 5 days` | Showing on a dashboard |
| `sensor.black_bin_days_until` | `0`, `1`, `5` (days) | Automations, e.g. a reminder when it is `1` |
| `sensor.black_bin_next_collection` | `2026-10-21` | The actual collection date |

There is also a `calendar.bin_collections` calendar with every collection as an all-day event, which shows in Home Assistant's calendar.

The sensors update at midnight, so "Tomorrow" changes to "Today" straight away.


## Bins out tonight

`binary_sensor.bins_out_tonight` turns on at 6pm the evening before any collection and off at 7am on collection day. Its `bins` attribute lists which bins are due, e.g. `["Black Bin", "Brown Bin"]`.

To change the 6pm time, go to Settings > Devices & services > Sheffield Bin Collections and click Configure.

Example reminder automation:

```yaml
automation:
  - alias: Put the bins out
    triggers:
      - trigger: state
        entity_id: binary_sensor.bins_out_tonight
        to: "on"
    actions:
      - action: notify.notify
        data:
          message: "Put out the {{ state_attr('binary_sensor.bins_out_tonight', 'bins') | join(' and ') }} tonight"
```


## Upgrading from 1.x

In 1.x the `Collection` sensor showed a number of days, and `Today` on collection day. It now always shows text (`Today`, `Tomorrow`, `In 5 days`), so any automation that compares it with a number should use the new `Days until` sensor instead. Existing entity IDs are kept.

If you don't have a green bin, the old Green Bin sensor will show as unavailable and can be deleted from Settings > Entities.


Warning!! We have no idea if the API will be switched off now the council has a new website, fingers crossed it's left operational.
