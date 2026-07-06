# Week 1 Deliverable — Orientation & Setup

**Project:** California Property Close Price Prediction — IDX Exchange SU26
**Intern:** Anvith Mulpuri
**Week:** 1 of 12
**Date Completed:** June 24, 2026
**Status:** ✅ Complete

---

## Overview

This document confirms the successful setup of the development environment and dataset access for the IDX Exchange Summer 2026 internship project. It also serves as the primary reference for understanding the CRMLS data fields that will be used throughout the 12-week close price prediction pipeline.

---

## Dataset Access Confirmation

### ✅ Access Status: CONFIRMED

| Item | Status | Details |
|---|---|---|
| Repository | ✅ Initialized | `IDX-Exchange-SU26-Anvith` cloned and configured |
| FTP Connection | ✅ Verified | FileZilla connected to IDX Exchange data server |
| Primary Dataset | ✅ Accessible | `CRMLSSold*` files located and downloaded |
| Metadata Reference | ✅ Reviewed | `Trestle Property MetaData.pdf` read in `/resources` |
| Storage Location | ✅ Confirmed | `/workspaces/IDX-Exchange-SU26-Anvith` |
| Data Format | ✅ Validated | CSV structure confirmed, field types reviewed |
| Access Permissions | ✅ Granted | Full read access; raw folder not modified |

### FTP Connection Details

| Setting | Value |
|---|---|
| Host | `199.250.207.194` |
| Port | `21` |
| Username | `data@idxexchange.com` |
| Directory | `/raw/California` |
| Files | `CRMLSSold*` prefix |

- Downloaded a minimum of **6 months** of sold listing data to local machine
- **No files in the raw folder were modified** — local copies only

---

## Tasks Completed

- [x] Repository initialization and setup
- [x] FTP connection established via FileZilla
- [x] `CRMLSSold*` dataset files located and downloaded (min. 6 months)
- [x] `Trestle Property MetaData.pdf` reviewed in `/resources`
- [x] Dataset structure and field types validated
- [x] Access permissions verified — read-only on raw folder
- [x] Development environment configured (Python, IDE/Colab)
- [x] Weekly deliverables folder structure established
- [x] Key column definitions documented (this file)

---

## Key Column Definitions

The following notes are derived from the **Trestle Property Metadata** and organized by category. The project filters exclusively on `PropertyType = Residential` and `PropertySubType = SingleFamilyResidence`.

---

### 🎯 Target Variable

| Field | Type | What It Means |
|---|---|---|
| `ClosePrice` | Decimal | **The target variable.** The final amount paid by the purchaser to the seller under the purchase agreement. This is the true transaction value — what the market actually paid, not what was asked. |

---

### 📋 Listing Identification

| Field | Type | What It Means |
|---|---|---|
| `ListingKey` | String (20) | The unique identifier for each listing record in the MLS system. Used as the primary key when joining or deduplicating records. |
| `ListingKeyNumeric` | Int64 | Numeric version of `ListingKey`. Useful for faster joins and indexing operations in pandas. |
| `ListingId` | String (255) | A human-readable listing identifier intended for display. In aggregated systems, this may not be globally unique — use `ListingKey` for programmatic joins. |

---

### 💰 Pricing Fields

| Field | Type | What It Means |
|---|---|---|
| `ListPrice` | Decimal | The seller's current asking price as set by the seller and their broker. This is a marketing price and reflects seller expectations, not market value. |
| `OriginalListPrice` | Decimal | The asking price at the time the listing agreement was first signed. Comparing this to `ListPrice` reveals whether a price reduction occurred before sale. |
| `ClosePrice` | Decimal | *(See Target Variable above)* |

> **Analyst Note:** The ratio of `ClosePrice` to `ListPrice` is the **sale-to-list ratio** — a key market health signal. A ratio above 1.0 indicates a competitive seller's market (sold above asking); below 1.0 suggests buyer leverage or an overpriced listing.

---

### 🏠 Property Characteristics

| Field | Type | What It Means |
|---|---|---|
| `PropertyType` | Enum | Broad category of the property (e.g., Residential, Commercial). **Filter to `Residential` for this project.** |
| `PropertySubType` | Enum | Sub-classification within the property type (e.g., SingleFamilyResidence, Condominium, Townhouse). **Filter to `SingleFamilyResidence` for this project.** |
| `LivingArea` | Decimal | Total livable interior square footage of the structure. One of the strongest predictors of close price. |
| `BuildingAreaTotal` | Decimal | Total area of the entire structure, including both finished and unfinished areas (e.g., garages, unfinished basements). Will typically be larger than `LivingArea`. |
| `AboveGradeFinishedArea` | Decimal | Finished square footage at or above ground level. Excludes basements. May be preferred over `LivingArea` in some markets. |
| `BelowGradeFinishedArea` | Decimal | Finished square footage below ground level (finished basements). May be zero or null for most California SFR properties. |
| `BedroomsTotal` | Int32 | Total number of bedrooms in the property. A core feature for price prediction. |
| `BathroomsTotalInteger` | Int32 | Simple integer count of all bathrooms (full + half counted together). For example, a home with 2 full and 1 half bath = 3. |
| `MainLevelBedrooms` | Int32 | Number of bedrooms on the main/entry floor. Useful for single-story vs. multi-story differentiation. |
| `Stories` | Int32 | Number of floors in the property. Correlates with size and sometimes price. |
| `Levels` | Enum | Descriptive version of floor count (e.g., "One Level", "Two Levels", "Multi/Split"). Overlaps with `Stories`; use one consistently. |
| `YearBuilt` | Int32 | The year the property first received an occupancy permit. Used to calculate **property age**, a useful engineered feature (`current_year - YearBuilt`). |
| `NewConstructionYN` | Boolean | Flags whether the property is newly built and previously unoccupied. New construction may behave differently in pricing models. |

---

### 🌳 Lot & Land

| Field | Type | What It Means |
|---|---|---|
| `LotSizeSquareFeet` | Decimal | Total lot area in square feet. A key feature for SFR properties where land size affects value. |
| `LotSizeAcres` | Decimal | Total lot area in acres. Redundant with `LotSizeSquareFeet` — use one consistently (square feet preferred for SFR). |
| `LotSizeArea` | Decimal | Raw lot size value; units defined by a separate `LotSizeUnits` field. Prefer `LotSizeSquareFeet` or `LotSizeAcres` for direct use. |
| `LotSizeDimensions` | String (150) | Freeform text describing lot shape/dimensions (e.g., "250 x 180"). Not reliable for modeling — use numeric area fields instead. |
| `SubdivisionName` | String (50) | Name of the neighborhood, community, or builder tract. Can be useful as a categorical geographic feature. |

---

### 📍 Location & Geography

| Field | Type | What It Means |
|---|---|---|
| `UnparsedAddress` | String (255) | Full property address as a single text field entered by the agent. Used for display and geocoding but not modeling directly. |
| `StreetNumberNumeric` | Int32 | The numeric portion of the street address. |
| `City` | String (50) | The city listed in the property address. Useful as a categorical geographic feature. |
| `StateOrProvince` | Enum | Postal abbreviation for the state (e.g., CA). All records in this project should be California. |
| `PostalCode` | String (10) | ZIP code. One of the most important geographic features — ZIP codes capture local market conditions effectively. |
| `CountyOrParish` | String (50) | The county the property is located in. A useful regional feature, coarser than ZIP code but finer than state. |
| `MLSAreaMajor` | String (50) | A major marketing area name defined by the MLS or a regional organization. Provides an alternative geographic grouping to ZIP or county. |
| `Latitude` | Decimal (12.8) | Geographic latitude of the property. Enables spatial analysis and distance-based features. |
| `Longitude` | Decimal (12.8) | Geographic longitude of the property. Paired with `Latitude` for mapping and the school district spatial join in Week 6. |

---

### 🏫 Schools

| Field | Type | What It Means |
|---|---|---|
| `ElementarySchool` | String (50) | Name of the elementary school in the property's catchment area. |
| `ElementarySchoolDistrict` | String (50) | Name of the elementary school district. |
| `MiddleOrJuniorSchool` | String (50) | Name of the junior/middle school in the catchment area. |
| `MiddleOrJuniorSchoolDistrict` | String (50) | Name of the junior/middle school district. |
| `HighSchool` | String (50) | Name of the high school in the catchment area. |
| `HighSchoolDistrict` | String (50) | Name of the high school district. When only one school district field is used, this is the preferred field. |

> **Week 6 Note:** These fields will be supplemented by a spatial join against the [CA School District Areas 2024–25](https://data.ca.gov/dataset/california-school-district-areas-2024-25) boundaries using `Latitude`/`Longitude`, providing a standardized, geometry-validated school district layer.

---

### 📅 Dates & Market Timing

| Field | Type | What It Means |
|---|---|---|
| `ListingContractDate` | DateTime | Date the listing agreement was signed between the seller and their broker — the official start of the listing period. Used to calculate Days on Market. |
| `PurchaseContractDate` | DateTime | Date the purchase offer was accepted and the property went under contract (Pending status). Typically 30–45 days before `CloseDate`. |
| `ContractStatusChangeDate` | DateTime | Date of any contractual status change in the listing. Not always the same as when the change was entered in the MLS. |
| `CloseDate` | DateTime | Date the transaction officially closed — funds transferred, deed recorded, ownership changed. **Only present in sold records.** |
| `DaysOnMarket` | Int32 | Number of days the listing was on market before going under contract, as calculated by the MLS. A key market health indicator; low DOM = high demand. |

---

### 🏗️ Amenities & Features

| Field | Type | What It Means |
|---|---|---|
| `GarageSpaces` | Decimal | Number of spaces in the garage(s). |
| `CoveredSpaces` | Decimal | Total number of covered parking spaces including garage and carport. |
| `ParkingTotal` | Decimal | Total parking spaces included in the sale (covered + uncovered). |
| `AttachedGarageYN` | Boolean | Whether any garage structure is directly attached to the main dwelling. |
| `FireplaceYN` | Boolean | Whether the property includes at least one fireplace. |
| `FireplacesTotal` | Int32 | Total count of fireplaces in the property. |
| `PoolPrivateYN` | Boolean | Whether the property has a privately owned pool included in the sale. |
| `BasementYN` | Boolean | Whether the property has a basement. Less common in California SFR but present in some areas. |
| `ViewYN` | Boolean | Whether the property has a notable view. Can be a meaningful price driver in scenic areas. |
| `WaterfrontYN` | Boolean | Whether the property is on the waterfront (ocean, lake, river, etc.). |
| `Flooring` | Enum | List of flooring types found in the property (e.g., hardwood, tile, carpet). |

---

### 💵 Taxes & HOA

| Field | Type | What It Means |
|---|---|---|
| `TaxAnnualAmount` | Decimal | The most recent annual property tax amount. Reflects assessed value and local tax rate — can be a proxy for property value in some cases. |
| `TaxYear` | Int32 | The year in which the `TaxAnnualAmount` assessment was made. |
| `AssociationFee` | Decimal | Monthly or recurring HOA fee paid by the homeowner. Affects buyer affordability calculations. |
| `AssociationFeeFrequency` | Enum | How often the HOA fee is paid (Monthly, Annually, etc.). Needed to normalize `AssociationFee` to a common period. |

---

### 👤 Agent & Brokerage

| Field | Type | What It Means |
|---|---|---|
| `ListAgentFirstName` | String (50) | First name of the listing (seller's) agent. |
| `ListAgentLastName` | String (50) | Last name of the listing agent. |
| `ListAgentFullName` | String (150) | Full name of the listing agent. |
| `ListAgentEmail` | String (80) | Email address of the listing agent. |
| `ListAgentAOR` | Enum | The Association of REALTORS® the listing agent belongs to. |
| `ListOfficeName` | String (255) | Legal name of the brokerage representing the seller. |
| `CoListAgentFirstName` | String (50) | First name of the co-listing agent (if applicable). |
| `CoListAgentLastName` | String (50) | Last name of the co-listing agent. |
| `CoListOfficeName` | String (255) | Legal name of the co-listing brokerage. |
| `BuyerAgentFirstName` | String (50) | First name of the buyer's agent. |
| `BuyerAgentLastName` | String (50) | Last name of the buyer's agent. |
| `BuyerAgentMlsId` | String (25) | The MLS identifier for the buyer's agent. |
| `BuyerAgentAOR` | Enum | The Association of REALTORS® the buyer's agent belongs to. |
| `BuyerOfficeName` | String (255) | Legal name of the brokerage representing the buyer. |
| `BuyerOfficeAOR` | Enum | The buyer's office's Association of REALTORS®. |
| `CoBuyerAgentFirstName` | String (50) | First name of the buyer's co-agent (if applicable). |

> **Analyst Note:** Agent/brokerage fields are not used as predictive features in the close price model but enable brokerage-level performance analysis — which offices close the most volume, which agents consistently achieve above-asking prices, and how market share is distributed across firms.

---

### 📊 MLS Status

| Field | Type | What It Means |
|---|---|---|
| `MlsStatus` | Enum | Local/regional MLS status (may vary by board). Each local status maps to a single `StandardStatus`. Used to track where a listing is in its lifecycle. |

> **Common Status Values:**
> - `Active` — property is live and available for offers
> - `Pending` — offer accepted; under contract, not yet closed
> - `Closed` — transaction complete; `ClosePrice` and `CloseDate` are populated
> - `Back on Market` — deal fell through; property returned to active
> - `Expired` — listing period ended without a sale
> - `Withdrawn` — seller pulled the listing before expiry
>
> **Always filter to `Closed` status when building price models.** Only closed records have a confirmed `ClosePrice`.

---

### 🏢 Other Fields

| Field | Type | What It Means |
|---|---|---|
| `BuilderName` | String (50) | Name of the builder or builder's tract. Relevant for new construction properties. |
| `BusinessType` | Enum | Type of business being sold (retail, wholesale, etc.). Not applicable to SFR — will be null for this project's filtered dataset. |

---

## Key Deliverables

### 1. Project Repository
- Successfully cloned and initialized at `/workspaces/IDX-Exchange-SU26-Anvith`
- README documentation complete with project overview, goals, and 12-week timeline
- Folder structure established for notebooks, data, deliverables, and app

### 2. Weekly Deliverables Structure
- `/weekly-deliverables/` folder created and organized
- Week 1 folder established with this document
- Documentation framework in place for Weeks 2–12

### 3. Dataset Verification
- All dataset paths confirmed accessible via FTP
- Minimum 6 months of `CRMLSSold*` data downloaded
- Field types and structure reviewed against Trestle metadata
- Data ready for EDA in Week 2

---

## Feature Candidates for the Model

The Trestle dataset contains **80+ fields** spanning pricing, property characteristics, geography, amenities, dates, agent relationships, and MLS status. Features most likely to be included in the initial model:

| Category | Fields |
|---|---|
| Size | `LivingArea`, `LotSizeSquareFeet`, `BuildingAreaTotal` |
| Layout | `BedroomsTotal`, `BathroomsTotalInteger`, `Stories` |
| Location | `PostalCode`, `CountyOrParish`, `Latitude`, `Longitude` |
| Condition / Age | `YearBuilt`, `NewConstructionYN` |
| Amenities | `PoolPrivateYN`, `GarageSpaces`, `ViewYN` |
| Market Timing | `DaysOnMarket`, `CloseDate` (month/season) |
| Price Signal | `ListPrice`, `OriginalListPrice` |
| Schools | `HighSchoolDistrict` (+ spatial join in Week 6) |

---

## Next Steps (Week 2)

- Load minimum 6 months of dataset into pandas
- Explore distributions of `ClosePrice`, `LivingArea`, `BedroomsTotal`, `BathroomsTotalInteger`, `LotSizeSquareFeet`
- Filter to `PropertyType = Residential` and `PropertySubType = SingleFamilyResidence`
- Produce `01_exploration.ipynb` with EDA plots and initial observations

---

## Sign-Off

**Prepared by:** Anvith Mulpuri
**Date Completed:** June 24, 2026
**Review Status:** ✅ Ready for Week 2
