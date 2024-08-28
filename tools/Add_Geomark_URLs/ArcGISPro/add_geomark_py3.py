r"""

Original Author: jeff.kruys@gov.bc.ca (FIRB) 

Created on:
2024-08-12

Purpose:
This script creates Geomark URLs for each feature in an input dataset, and 
writes them to a new field named GeomarkURL. It can be run at the command
prompt on a system with ArcGIS Pro installed, or directly in ArcGIS Pro in a 
script tool named Add_Geomark_URL in a toolbox named Add_Geomark_URL.atbx.

Usage:
add_geomark_py3.py lyr

Positional Arguments:
   lyr              Input layer

Requirements:
ArcGIS Pro

Example Input:
X:\fullpath\add_geomark_py3.py Y:\fullpath\lyr

History
2024-08-12 (JK): Created script.
2024-08-20 (JK): Changed added field name from Geomark_URL to GeomarkURL to fit
                 within shapefile field name length limitation. Also modified 
                 to write URL to GeomarkURL field if current value of field is
                 either None, "" or " ".
2024-08-26 (JK): Added try and else clauses to write error messages to output
                 field
"""

import arcpy, requests, time

def add_geomark_url(in_fc):

    # Get the spatial reference of the input dataset
    srid = arcpy.da.Describe(in_fc)["spatialReference"].factoryCode
    arcpy.AddMessage(time.strftime('%Y-%m-%d %H:%M:%S : ') + f"Spatial reference code of input dataset: {srid}")

    # Add GeomarkURL field if it doesn't already exist
    flist = [f.name for f in arcpy.ListFields(in_fc)]
    if "GeomarkURL" not in flist:
        arcpy.management.AddField(in_table=in_fc, field_name="GeomarkURL", field_type="TEXT", field_length=100)
        arcpy.AddMessage(time.strftime('%Y-%m-%d %H:%M:%S : ') + "Added GeomarkURL field to input layer")
    else:
        arcpy.AddMessage(time.strftime('%Y-%m-%d %H:%M:%S : ') + "GeomarkURL field already exists in input layer")

    # Read each record, send request to create Geomark URL, write the returned URL to the GeomarkURL field
    row_total = int(arcpy.GetCount_management(in_fc).getOutput(0))
    read_count = 0
    update_count = 0
    arcpy.AddMessage(time.strftime('%Y-%m-%d %H:%M:%S : ') + f"Processing {row_total} feature(s) of input dataset")
    session = requests.Session()
    with arcpy.da.UpdateCursor(in_fc, ["GeomarkURL", "SHAPE@"]) as cursor:
        for row in cursor:
            read_count += 1
            exist_url = row[0]
            if exist_url is None or exist_url in ["", " "]:
                geom = row[1]
                if geom is None:
                    row[0] = "Null geometry"
                else:
                    geom_wkt = geom.WKT
                    post_url = "https://apps.gov.bc.ca/pub/geomark/geomarks/new"
                    payload = {"bufferSegments": 8, "body": geom_wkt, "bufferMetres": None, "callback": None, 
                               "failureRedirectUrl": None, "bufferJoin": "ROUND", "bufferMitreLimit": 5, 
                               "bufferCap": "ROUND", "redirectUrl": None, "resultFormat": None, "format": "wkt", 
                               "srid": srid, "allowOverlap": "false"}
                    try:
                        r = session.post(post_url, data=payload, timeout=5)
                    except:
                        row[0] = "Geomark Web Service request failed - try running the tool again"
                    if r.status_code == 200:
                        out_url = r.url
                        if out_url == "https://apps.gov.bc.ca/pub/geomark/geomarks/new":
                            row[0] = "Could not create Geomark URL for this geometry"
                        else:
                            row[0] = out_url
                            update_count += 1
                    else:
                        row[0] = f"Geomark Web Service returned status code {r.status_code}; try running the tool again"
                cursor.updateRow(row)

            if read_count % 10 == 0 or read_count == row_total:
                arcpy.AddMessage(time.strftime('%Y-%m-%d %H:%M:%S : ') + f"Processed {read_count} of {row_total} "
                      f"feature(s) and added Geomark URL to {update_count} feature(s)")

if __name__ == "__main__":
    in_fc = arcpy.GetParameterAsText(0)
    add_geomark_url(in_fc)
