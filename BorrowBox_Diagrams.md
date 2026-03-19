# BorrowBox (Online Renting System) - Software Diagrams

This document contains simple, professional, and editable diagrams based on your Django models and project architecture. 

### How to use and edit these diagrams:
1. **Markdown Viewers:** If you are using VS Code or GitHub, these will automatically render as diagrams.
2. **draw.io / diagrams.net:** Open [draw.io](https://app.diagrams.net/), click **Arrange** > **Insert** > **Advanced** > **Mermaid...** and paste the code block text inside.
3. **Mermaid Live Editor:** Copy the code block starting with `erDiagram` or `flowchart` and paste it into [Mermaid Live Editor](https://mermaid.live/) to view, tweak, and export as PNG or SVG.

---

## 1. Entity-Relationship (ER) Diagram (Chen's Notation)
This outlines the core entities, their attributes, and relationships mapping exactly to the visual style you requested.

```mermaid
flowchart TD
    %% Define styles for Chen's notation
    classDef entity fill:#3498db,stroke:#2980b9,stroke-width:2px,color:#fff;
    classDef attribute fill:#82e0aa,stroke:#2ecc71,stroke-width:2px,color:#000;
    classDef relationship fill:#f39c12,stroke:#d35400,stroke-width:2px,color:#fff;

    %% Entities (Rectangles)
    USER[User]:::entity
    PROFILE[Profile]:::entity
    ITEM[Item]:::entity
    BOOKING[Booking]:::entity
    CATEGORY[Category]:::entity

    %% Relationships (Diamonds)
    HAS{has}:::relationship
    OWNS{owns}:::relationship
    MAKES{makes}:::relationship
    CONTAINS{contains}:::relationship
    RECEIVES{receives}:::relationship

    %% Attributes for USER (Ovals)
    u_id([ID]):::attribute
    u_uname([Username]):::attribute
    u_email([Email]):::attribute

    %% Attributes for PROFILE (Ovals)
    p_seller([Is Seller]):::attribute
    p_status([Seller Status]):::attribute
    p_phone([Phone]):::attribute

    %% Attributes for ITEM (Ovals)
    i_title([Title]):::attribute
    i_price([Price/Day]):::attribute
    i_loc([Location]):::attribute

    %% Attributes for BOOKING (Ovals)
    b_date([Dates]):::attribute
    b_price([Total Price]):::attribute
    b_status([Status]):::attribute

    %% Attributes for CATEGORY (Ovals)
    c_id([ID]):::attribute
    c_name([Name]):::attribute

    %% Link Entities and Relationships
    USER ---|1| HAS
    HAS ---|1| PROFILE

    USER ---|1| OWNS
    OWNS ---|N| ITEM

    USER ---|1| MAKES
    MAKES ---|N| BOOKING

    CATEGORY ---|1| CONTAINS
    CONTAINS ---|N| ITEM

    ITEM ---|1| RECEIVES
    RECEIVES ---|N| BOOKING

    %% Link Entities to Attributes
    USER --- u_id
    USER --- u_uname
    USER --- u_email

    PROFILE --- p_seller
    PROFILE --- p_status
    PROFILE --- p_phone

    ITEM --- i_title
    ITEM --- i_price
    ITEM --- i_loc

    BOOKING --- b_date
    BOOKING --- b_price
    BOOKING --- b_status

    CATEGORY --- c_id
    CATEGORY --- c_name
```

---

## 2. Use Case Diagram
This maps out what different users (actors) can accomplish inside the system. 

```mermaid
flowchart LR
    %% Actors
    Guest([Guest User])
    RegUser([Registered User])
    Seller([Approved Seller])
    Admin([System Admin])

    %% System Boundary
    subgraph BorrowBox System
        UC1(Browse Categories & Items)
        UC2(Register / Login)
        UC3(Book an Item)
        UC4(Manage Profile)
        UC5(Apply for Seller Status)
        UC6(Publish / Edit Items)
        UC7(Manage Bookings)
        UC8(Approve Sellers)
        UC9(Manage Categories)
    end

    %% Relationships
    Guest --> UC1
    Guest --> UC2
    
    RegUser --> UC1
    RegUser --> UC3
    RegUser --> UC4
    RegUser --> UC5
    RegUser --> UC7
    
    Seller --> UC4
    Seller --> UC6
    Seller --> UC7
    
    Admin --> UC8
    Admin --> UC9
    Admin --> UC1
```

---

## 3. Data Flow Diagram (DFD)

### Level 0 DFD (Context Diagram)
This shows the system as a single process interacting with external entities.

```mermaid
%%{init: {"flowchart": {"curve": "stepBefore"}}}%%
flowchart TD
    %% External Entities
    usr[User / Customer]
    sel[Seller]
    adm[Admin]

    %% System Process
    system((BorrowBox\nOnline Renting\nSystem))

    %% Data Flows
    usr -- Item Search, Booking Request --> system
    system -- Display Items, Booking Confirmation --> usr
    
    sel -- Item Details, Application --> system
    system -- Item Status, Account Approval --> sel
    
    adm -- Approval Actions, Category Updates --> system
    system -- System Reports, User Data --> adm
```

### Level 1 DFD
This breaks down the system into the main sub-processes.

```mermaid
%%{init: {"flowchart": {"curve": "stepBefore"}}}%%
flowchart TD
    %% External Entities
    usr[User]
    sel[Seller]
    adm[Admin]

    %% Processes
    P1((1.0\nUser & Profile\nManagement))
    P2((2.0\nSeller Approval\nSystem))
    P3((3.0\nItem\nManagement))
    P4((4.0\nBooking\nManagement))

    %% Data Stores
    D1[(D1: Users DB)]
    D2[(D2: Items DB)]
    D3[(D3: Bookings DB)]

    %% User interactions
    usr -- Credentials, Profile Data --> P1
    P1 -- Auth Status --> usr
    P1 <--> D1
    
    %% Seller application flow
    usr -- Application Request --> P2
    P2 -- Application Status --> usr
    adm -- Approve/Reject --> P2
    P2 <--> D1

    %% Item management interactions
    sel -- Item Details --> P3
    usr -- Search Criteria --> P3
    P3 -- Displayed Item List --> usr
    P3 <--> D2
    
    %% Booking management interactions
    usr -- Booking Info, Dates --> P4
    P4 -- Booking Status (Confirmed/Expired) --> usr
    P4 <--> D3
    P3 -. Verify Item Availability .-> P4
```
