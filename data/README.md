# Data Directory

Raw CSV files go in this directory. They are not synced to GitHub. 

## Data Dictionary

Metadata about this dataset, Traffic Accidents (Offenses) from the City of Denver.

### `objectid_1`
Record identification number used in this dataset

### `incident_id`
Official record identification number assigned by the Denver Police Department

### `offense_id`
Concatenation of `INCIDENT_ID`, `OFFENSE_CODE`, and `OFFENSE_CODE_EXTENSION`

### `offense_code`
Code indicating the type of offense

### `offense_code_extension`
Code indicating the offense subtype, if applicable

### `top_traffic_accident_offense`
The most significant motor vehicle accident offense associated with the crash (in order, most to least): FATAL, SBI, HIT & RUN, DUI, POLICE, ACCIDENT

### `first_occurrence_date`
Earliest potential date and time of reported crash (In some cases, like a hit and run crash involving a parked vehicle, the reporting vehicle owner may not know the exact time of occurrence.)

### `last_occurrence_date`
Latest potential date and time of reported crash (In some cases, like a hit and run crash involving a parked vehicle, the reporting vehicle owner may not know the exact time of occurrence.)

### `reported_date`
Date and time the crash was reported to DPD

### `incident_address`
Approximate location of the incident

### `geo_x`
Approximate horizontal location (east-west) of crash defined in the NAD 1983 State Plane feet Colorado Central FIPS 0502 projected coordinate system

### `geo_y`
Approximate vertical location (north-south) of crash defined in the NAD 1983 State Plane feet Colorado Central FIPS 0502 projected coordinate system

### `geo_lon`
Approximate horizontal location (east-west) of crash defined in WGS 1984 geographic coordinate system

### `geo_lat`
Approximate vertical location (north-south) of crash defined in WGS 1984 geographic coordinate system

### `district_id`
Denver Police District where the crash occurred

### `precinct_id`
Denver Police Precinct where the crash occurred

### `neighborhood_id`
Neighborhood where the crash occurred

### `bicycle_ind`
Indicates how many people riding bicycles were involved with the crash

### `pedestrian_ind`
Indicates how many pedestrians were involved with the crash

### `harmful_event_seq_1`
Indicates the first occurring harmful event in the crash

### `harmful_event_seq_2`
Indicates the second occurring harmful event in the crash

### `harmful_event_seq_3`
Indicates the most harmful event in the crash

### `road_location`
Describes the specific location of the crash in relation to the roadway or if on private property

### `road_description`
Describes the specific location of the crash in relation to intersections, alleys, driveways, highway interchanges, and parking lots

### `road_contour`
Describes the specific location of the crash relating to horizonal and vertical curves at the location of the first harmful event

### `road_condition`
Describes the roadway conditions at the time and location of the crash

### `light_condition`
Describes the roadway lighting conditions at the time and location of the crash

### `tu1_vehicle_type`
Indicates the vehicle type of traffic unit 1

### `tu1_travel_direction`
Indicates the vehicle direction prior to impact of traffic unit 1

### `tu1_vehicle_movement`
Indicates the vehicle movement prior to impact of traffic unit 1

### `tu1_driver_action`
Indicates any action contibuting to the crash by the driver of traffic unit 1, when applicable

### `tu1_driver_humancontribfactor`
Indicates any additional contributing factor to the crash by the driver of traffic unit 1, when applicable

### `tu1_pedestrian_action`
Indicates any action contibuting to the crash by a pedestrian traffic unit 1, when applicable

### `tu2_vehicle_type`
Indicates the vehicle type of traffic unit 2

### `tu2_travel_direction`
Indicates the vehicle direction prior to impact of traffic unit 2

### `tu2_vehicle_movement`
Indicates the vehicle movement prior to impact of traffic unit 2

### `tu2_driver_action`
Indicates any action contibuting to the crash by the driver of traffic unit 2, when applicable

### `tu2_driver_humancontribfactor`
Indicates any additional contributing factor to the crash by the driver of traffic unit 2, when applicable

### `tu2_pedestrian_action`
Indicates any action contibuting to the crash by a pedestrian traffic unit 2, when applicable

### `seriously_injured`
Indicates the number of people who were seriously injured as a result of the crash

### `fatalities`
Indicates the number of people who were fatally injured as a result of the crash

### `fatality_mode_1`
Indicates the mode (means of travel) of a person fatally injured as a result of the crash, not related to traffic unit number

### `fatality_mode_2`
Indicates the mode (means of travel) of a second person fatally injured as a result of the crash, not related to traffic unit number

### `seriously_injured_mode_1`
Indicates the mode (means of travel) of a person seriously injured as a result of the crash, not related to traffic unit number

### `seriously_injured_mode_2`
Indicates the mode (means of travel) of a second person seriously injured as a result of the crash, not related to traffic unit number  