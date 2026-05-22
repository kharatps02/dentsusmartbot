/*******************************************************************************
   Dentsu Marketing & Advertising Database - Version 1.0
   Script: dentsu_marketing_advertising_create_script.sql
   Description: Creates and populates a sample Dentsu-themed marketing and advertising database.
   DB Server: SQLite
   Note: Sample clients, campaigns, invoices, and employee records are fictional demo data.
********************************************************************************/

/*******************************************************************************
   Drop Tables
********************************************************************************/
DROP TABLE IF EXISTS [InvoiceLineItems];
DROP TABLE IF EXISTS [Invoice];
DROP TABLE IF EXISTS [CampaignPlacement];
DROP TABLE IF EXISTS [Campaign];
DROP TABLE IF EXISTS [MediaChannel];
DROP TABLE IF EXISTS [Client];
DROP TABLE IF EXISTS [Employee];
DROP TABLE IF EXISTS [Office];

/*******************************************************************************
   Create Tables
********************************************************************************/
CREATE TABLE [Office] (
    [OfficeId] INTEGER NOT NULL,
    [Name] NVARCHAR(100) NOT NULL,
    [City] NVARCHAR(50) NOT NULL,
    [State] NVARCHAR(50),
    [Country] NVARCHAR(50) NOT NULL,
    [PostalCode] NVARCHAR(15),
    CONSTRAINT [PK_Office] PRIMARY KEY ([OfficeId])
);

CREATE TABLE [Employee] (
    [EmployeeId] INTEGER NOT NULL,
    [FirstName] NVARCHAR(50) NOT NULL,
    [LastName] NVARCHAR(50) NOT NULL,
    [Title] NVARCHAR(75),
    [OfficeId] INTEGER NOT NULL,
    [HireDate] DATETIME,
    [Email] NVARCHAR(100),
    [Phone] NVARCHAR(20),
    CONSTRAINT [PK_Employee] PRIMARY KEY ([EmployeeId]),
    FOREIGN KEY ([OfficeId]) REFERENCES [Office] ([OfficeId])
);

CREATE TABLE [Client] (
    [ClientId] INTEGER NOT NULL,
    [CompanyName] NVARCHAR(100) NOT NULL,
    [Industry] NVARCHAR(75),
    [Country] NVARCHAR(50),
    [AccountStartYear] INTEGER,
    CONSTRAINT [PK_Client] PRIMARY KEY ([ClientId])
);

CREATE TABLE [Campaign] (
    [CampaignId] INTEGER NOT NULL,
    [CampaignName] NVARCHAR(150) NOT NULL,
    [ClientId] INTEGER NOT NULL,
    [Objective] NVARCHAR(100),
    [Budget] NUMERIC(12, 2) NOT NULL,
    [LaunchDate] DATETIME,
    CONSTRAINT [PK_Campaign] PRIMARY KEY ([CampaignId]),
    FOREIGN KEY ([ClientId]) REFERENCES [Client] ([ClientId])
);

CREATE TABLE [MediaChannel] (
    [ChannelId] INTEGER NOT NULL,
    [ChannelName] NVARCHAR(100) NOT NULL,
    [ChannelType] NVARCHAR(50) NOT NULL,
    [Region] NVARCHAR(50),
    CONSTRAINT [PK_MediaChannel] PRIMARY KEY ([ChannelId])
);

CREATE TABLE [CampaignPlacement] (
    [PlacementId] INTEGER NOT NULL,
    [CampaignId] INTEGER NOT NULL,
    [ChannelId] INTEGER NOT NULL,
    [OfficeId] INTEGER NOT NULL,
    [ImpressionsBooked] INTEGER NOT NULL,
    CONSTRAINT [PK_CampaignPlacement] PRIMARY KEY ([PlacementId]),
    FOREIGN KEY ([CampaignId]) REFERENCES [Campaign] ([CampaignId]),
    FOREIGN KEY ([ChannelId]) REFERENCES [MediaChannel] ([ChannelId]),
    FOREIGN KEY ([OfficeId]) REFERENCES [Office] ([OfficeId])
);

CREATE TABLE [Invoice] (
    [InvoiceId] INTEGER NOT NULL,
    [ClientId] INTEGER NOT NULL,
    [EmployeeId] INTEGER,
    [InvoiceDate] DATETIME NOT NULL,
    [TotalAmount] NUMERIC(12, 2) NOT NULL,
    CONSTRAINT [PK_Invoice] PRIMARY KEY ([InvoiceId]),
    FOREIGN KEY ([ClientId]) REFERENCES [Client] ([ClientId]),
    FOREIGN KEY ([EmployeeId]) REFERENCES [Employee] ([EmployeeId])
);

CREATE TABLE [InvoiceLineItems] (
    [LineItemId] INTEGER NOT NULL,
    [InvoiceId] INTEGER NOT NULL,
    [CampaignId] INTEGER NOT NULL,
    [ServiceDescription] NVARCHAR(150) NOT NULL,
    [Quantity] INTEGER NOT NULL,
    [UnitPrice] NUMERIC(12, 2) NOT NULL,
    CONSTRAINT [PK_InvoiceLineItems] PRIMARY KEY ([LineItemId]),
    FOREIGN KEY ([InvoiceId]) REFERENCES [Invoice] ([InvoiceId]),
    FOREIGN KEY ([CampaignId]) REFERENCES [Campaign] ([CampaignId])
);

/*******************************************************************************
   Populate Tables
********************************************************************************/
INSERT INTO [Office] ([OfficeId], [Name], [City], [State], [Country], [PostalCode]) VALUES
    (1, 'Dentsu Creative New York', 'New York', 'NY', 'USA', '10001'),
    (2, 'Dentsu Media Los Angeles', 'Los Angeles', 'CA', 'USA', '90001'),
    (3, 'Dentsu CXM Chicago', 'Chicago', 'IL', 'USA', '60601'),
    (4, 'Dentsu APAC Mumbai', 'Mumbai', 'MH', 'India', '400001'),
    (5, 'Dentsu EMEA London', 'London', NULL, 'United Kingdom', 'EC1A');

INSERT INTO [Employee] ([EmployeeId], [FirstName], [LastName], [Title], [OfficeId], [HireDate], [Email], [Phone]) VALUES
    (1, 'Aarav', 'Mehta', 'Account Director', 4, '2015-06-01', 'aarav.mehta@dentsu.example', '+91-22-5555-1001'),
    (2, 'Jane', 'Smith', 'Media Planner', 1, '2017-09-15', 'jane.smith@dentsu.example', '+1-212-555-1002'),
    (3, 'Alice', 'Brown', 'Performance Marketing Lead', 2, '2018-03-12', 'alice.brown@dentsu.example', '+1-310-555-1003'),
    (4, 'Michael', 'Clark', 'Creative Strategy Manager', 2, '2016-02-20', 'michael.clark@dentsu.example', '+1-310-555-1004'),
    (5, 'Emily', 'White', 'Client Success Manager', 3, '2019-07-10', 'emily.white@dentsu.example', '+1-312-555-1005'),
    (6, 'Priya', 'Nair', 'Brand Strategist', 4, '2020-01-15', 'priya.nair@dentsu.example', '+91-22-5555-1006'),
    (7, 'Oliver', 'Grant', 'Programmatic Specialist', 5, '2021-04-01', 'oliver.grant@dentsu.example', '+44-20-5555-1007'),
    (8, 'Maya', 'Kapoor', 'SEO Consultant', 4, '2022-08-18', 'maya.kapoor@dentsu.example', '+91-22-5555-1008');

INSERT INTO [Client] ([ClientId], [CompanyName], [Industry], [Country], [AccountStartYear]) VALUES
    (1, 'Aurora Electronics', 'Consumer Electronics', 'USA', 2019),
    (2, 'BlueWave Beverages', 'FMCG', 'USA', 2020),
    (3, 'UrbanTrail Apparel', 'Retail Fashion', 'USA', 2018),
    (4, 'Nimbus Bank', 'Financial Services', 'United Kingdom', 2017),
    (5, 'GreenLeaf Foods', 'Packaged Foods', 'India', 2021),
    (6, 'VoltAuto Mobility', 'Automotive', 'Germany', 2022),
    (7, 'HealthFirst Clinics', 'Healthcare', 'USA', 2020),
    (8, 'EduSphere Learning', 'EdTech', 'India', 2023),
    (9, 'SkyStay Hotels', 'Travel & Hospitality', 'Singapore', 2019),
    (10, 'MetroMart Retail', 'E-commerce', 'India', 2018),
    (11, 'Zenith Insurance', 'Insurance', 'USA', 2016),
    (12, 'PureGlow Beauty', 'Beauty & Personal Care', 'France', 2021),
    (13, 'FarmFresh Organics', 'Agriculture', 'India', 2020),
    (14, 'CodeCraft SaaS', 'Technology', 'USA', 2022),
    (15, 'PeakFit Gyms', 'Fitness', 'USA', 2023),
    (16, 'Luma Home Decor', 'Home & Living', 'United Kingdom', 2021),
    (17, 'SwiftPay Wallet', 'FinTech', 'India', 2022),
    (18, 'Oceanic Airlines', 'Aviation', 'UAE', 2019),
    (19, 'BrightKids Toys', 'Toys & Games', 'USA', 2017),
    (20, 'TerraSolar Energy', 'Renewable Energy', 'Australia', 2020);

INSERT INTO [Campaign] ([CampaignId], [CampaignName], [ClientId], [Objective], [Budget], [LaunchDate]) VALUES
    (1, 'Aurora Smart Home Launch', 1, 'Product Launch', 250000.00, '2023-01-07'),
    (2, 'BlueWave Summer Refresh', 2, 'Brand Awareness', 180000.00, '2023-02-01'),
    (3, 'UrbanTrail Street Style', 3, 'Sales Activation', 145000.00, '2023-02-14'),
    (4, 'Nimbus Digital Banking Push', 4, 'Lead Generation', 300000.00, '2023-03-01'),
    (5, 'GreenLeaf Better Breakfast', 5, 'Brand Awareness', 120000.00, '2023-03-10'),
    (6, 'VoltAuto EV Week', 6, 'Product Consideration', 450000.00, '2023-04-05'),
    (7, 'HealthFirst Preventive Care', 7, 'Community Education', 95000.00, '2023-04-15'),
    (8, 'EduSphere Exam Ready', 8, 'App Installs', 110000.00, '2023-05-01'),
    (9, 'SkyStay Weekend Escapes', 9, 'Bookings', 175000.00, '2023-05-12'),
    (10, 'MetroMart Big Basket Days', 10, 'Revenue Growth', 260000.00, '2023-06-01'),
    (11, 'Zenith Secure Tomorrow', 11, 'Lead Generation', 140000.00, '2023-06-15'),
    (12, 'PureGlow Radiance Month', 12, 'Influencer Engagement', 160000.00, '2023-07-01'),
    (13, 'FarmFresh Direct to Door', 13, 'Subscription Growth', 90000.00, '2023-07-10'),
    (14, 'CodeCraft DevOps Webinar', 14, 'B2B Pipeline', 85000.00, '2023-08-01'),
    (15, 'PeakFit New Year Prep', 15, 'Membership Growth', 105000.00, '2023-08-15'),
    (16, 'Luma Cozy Homes', 16, 'Seasonal Sales', 130000.00, '2023-09-01'),
    (17, 'SwiftPay Merchant Boost', 17, 'Merchant Acquisition', 220000.00, '2023-09-18'),
    (18, 'Oceanic Fly More', 18, 'Route Promotion', 380000.00, '2023-10-01'),
    (19, 'BrightKids Holiday Magic', 19, 'Holiday Sales', 210000.00, '2023-10-20'),
    (20, 'TerraSolar Clean Future', 20, 'Corporate Reputation', 195000.00, '2023-11-01'),
    (21, 'Aurora Upgrade Season', 1, 'Customer Retention', 125000.00, '2024-01-05'),
    (22, 'BlueWave Zero Sugar Trial', 2, 'Sampling', 135000.00, '2024-01-20'),
    (23, 'UrbanTrail App Exclusive', 3, 'App Revenue', 98000.00, '2024-02-01'),
    (24, 'Nimbus Wealth Webinar', 4, 'High Value Leads', 175000.00, '2024-02-15'),
    (25, 'GreenLeaf Healthy Snacking', 5, 'Retail Lift', 115000.00, '2024-03-01'),
    (26, 'VoltAuto Fleet Solutions', 6, 'B2B Pipeline', 325000.00, '2024-03-15'),
    (27, 'HealthFirst Telehealth Now', 7, 'Appointment Bookings', 150000.00, '2024-04-01'),
    (28, 'EduSphere Parent Trust', 8, 'Brand Trust', 70000.00, '2024-04-20'),
    (29, 'SkyStay Rewards Relaunch', 9, 'Loyalty Signups', 165000.00, '2024-05-01'),
    (30, 'MetroMart Festive Mega Sale', 10, 'Marketplace GMV', 500000.00, '2024-05-15');

INSERT INTO [MediaChannel] ([ChannelId], [ChannelName], [ChannelType], [Region]) VALUES
    (1, 'Google Search', 'Search', 'Global'),
    (2, 'YouTube', 'Video', 'Global'),
    (3, 'Meta Ads', 'Social', 'Global'),
    (4, 'Instagram Reels', 'Social Video', 'Global'),
    (5, 'LinkedIn Sponsored Content', 'B2B Social', 'Global'),
    (6, 'Programmatic Display Network', 'Display', 'Global'),
    (7, 'Connected TV', 'CTV', 'USA'),
    (8, 'Digital Out-of-Home', 'OOH', 'Urban Markets'),
    (9, 'Retail Media Network', 'Retail Media', 'India'),
    (10, 'Influencer Partnerships', 'Creator Marketing', 'Global');

INSERT INTO [CampaignPlacement] ([PlacementId], [CampaignId], [ChannelId], [OfficeId], [ImpressionsBooked]) VALUES
    (1, 1, 2, 1, 1200000),
    (2, 1, 6, 1, 900000),
    (3, 2, 3, 2, 1500000),
    (4, 2, 8, 2, 650000),
    (5, 3, 4, 2, 1100000),
    (6, 3, 10, 2, 450000),
    (7, 4, 1, 5, 800000),
    (8, 4, 5, 5, 300000),
    (9, 5, 9, 4, 700000),
    (10, 5, 3, 4, 950000),
    (11, 6, 7, 5, 1300000),
    (12, 6, 6, 5, 1000000),
    (13, 7, 1, 3, 300000),
    (14, 7, 3, 3, 600000),
    (15, 8, 1, 4, 500000),
    (16, 8, 4, 4, 900000),
    (17, 9, 2, 5, 700000),
    (18, 9, 6, 5, 850000),
    (19, 10, 9, 4, 1400000),
    (20, 10, 3, 4, 2000000),
    (21, 11, 1, 1, 350000),
    (22, 11, 5, 1, 220000),
    (23, 12, 10, 5, 600000),
    (24, 12, 4, 5, 1250000),
    (25, 13, 9, 4, 500000),
    (26, 13, 3, 4, 450000),
    (27, 14, 5, 1, 180000),
    (28, 14, 1, 1, 250000),
    (29, 15, 3, 3, 750000),
    (30, 15, 8, 3, 400000),
    (31, 16, 6, 5, 650000),
    (32, 16, 4, 5, 500000),
    (33, 17, 1, 4, 800000),
    (34, 17, 9, 4, 900000),
    (35, 18, 7, 5, 1600000),
    (36, 18, 2, 5, 1100000),
    (37, 19, 10, 1, 850000),
    (38, 19, 3, 1, 1200000),
    (39, 20, 5, 5, 350000),
    (40, 20, 6, 5, 650000),
    (41, 21, 1, 1, 450000),
    (42, 22, 10, 2, 500000),
    (43, 23, 4, 2, 700000),
    (44, 24, 5, 5, 200000),
    (45, 25, 9, 4, 780000),
    (46, 26, 5, 5, 260000),
    (47, 27, 1, 3, 600000),
    (48, 28, 3, 4, 550000),
    (49, 29, 2, 5, 750000),
    (50, 30, 9, 4, 2500000);

INSERT INTO [Invoice] ([InvoiceId], [ClientId], [EmployeeId], [InvoiceDate], [TotalAmount]) VALUES
    (1, 1, 1, '2023-01-15', 54970.00),
    (2, 2, 2, '2023-01-20', 49970.00),
    (3, 3, 3, '2023-01-25', 59970.00),
    (4, 4, 4, '2023-01-30', 45980.00),
    (5, 5, 5, '2023-02-05', 29970.00),
    (6, 6, 1, '2023-02-10', 74970.00),
    (7, 7, 2, '2023-02-15', 64970.00),
    (8, 8, 3, '2023-02-20', 49990.00),
    (9, 9, 4, '2023-02-25', 49970.00),
    (10, 10, 5, '2023-03-01', 65980.00),
    (11, 11, 1, '2023-03-05', 35980.00),
    (12, 12, 2, '2023-03-10', 44970.00),
    (13, 13, 3, '2023-03-15', 64990.00),
    (14, 14, 4, '2023-03-20', 39970.00),
    (15, 15, 5, '2023-03-25', 49970.00),
    (16, 16, 1, '2023-03-30', 89970.00),
    (17, 17, 2, '2023-04-05', 74970.00),
    (18, 18, 3, '2023-04-10', 59990.00),
    (19, 19, 4, '2023-04-15', 64990.00),
    (20, 20, 5, '2023-04-20', 45980.00);

INSERT INTO [InvoiceLineItems] ([LineItemId], [InvoiceId], [CampaignId], [ServiceDescription], [Quantity], [UnitPrice]) VALUES
    (1, 1, 1, 'Creative concept development', 1, 19990.00),
    (2, 1, 2, 'Paid social media planning', 2, 14990.00),
    (3, 2, 3, 'Influencer campaign setup', 1, 24990.00),
    (4, 2, 4, 'Search campaign optimization', 1, 24980.00),
    (5, 3, 5, 'Retail media activation', 2, 29990.00),
    (6, 3, 6, 'Programmatic display management', 1, 29980.00),
    (7, 4, 7, 'Healthcare content strategy', 2, 22990.00),
    (8, 4, 8, 'App install campaign launch', 1, 22990.00),
    (9, 5, 9, 'Travel video editing package', 2, 14990.00),
    (10, 6, 10, 'E-commerce performance sprint', 2, 29990.00),
    (11, 6, 11, 'Lead nurture email design', 1, 14990.00),
    (12, 7, 12, 'Creator outreach management', 1, 24990.00),
    (13, 7, 13, 'Subscription landing page testing', 1, 14990.00),
    (14, 8, 14, 'B2B webinar promotion', 1, 24990.00),
    (15, 8, 15, 'Fitness conversion funnel audit', 1, 24990.00),
    (16, 9, 16, 'Seasonal display creative', 2, 24990.00),
    (17, 9, 17, 'Merchant acquisition search setup', 1, 24990.00),
    (18, 10, 18, 'CTV media buying support', 2, 24990.00),
    (19, 10, 19, 'Holiday social creative pack', 1, 16990.00),
    (20, 10, 20, 'Corporate reputation messaging', 1, 24990.00),
    (21, 11, 21, 'Customer retention analytics', 2, 14990.00),
    (22, 11, 22, 'Sampling campaign reporting', 1, 19990.00),
    (23, 12, 23, 'App exclusive promotion setup', 1, 24990.00),
    (24, 12, 24, 'Wealth webinar lead scoring', 1, 19980.00),
    (25, 13, 25, 'Retail lift measurement', 2, 29990.00),
    (26, 13, 26, 'Fleet solutions B2B media', 2, 17990.00),
    (27, 14, 27, 'Telehealth appointment search ads', 1, 24990.00),
    (28, 14, 28, 'Parent trust brand study', 1, 14980.00),
    (29, 15, 29, 'Loyalty relaunch creative', 2, 24990.00),
    (30, 15, 30, 'Festive sale marketplace assets', 1, 19980.00),
    (31, 16, 1, 'Integrated launch campaign management', 3, 29990.00),
    (32, 16, 2, 'Social listening and insights', 2, 14990.00),
    (33, 17, 3, 'Street style creator content', 1, 24990.00),
    (34, 17, 4, 'Banking lead generation optimization', 1, 24990.00),
    (35, 18, 5, 'Better breakfast commerce media', 2, 24990.00),
    (36, 18, 6, 'EV week video production', 2, 19990.00),
    (37, 19, 7, 'Preventive care community ads', 2, 29990.00),
    (38, 19, 8, 'Exam ready performance reporting', 1, 14990.00),
    (39, 20, 9, 'Weekend escapes travel retargeting', 1, 24990.00),
    (40, 20, 10, 'Big Basket Days conversion audit', 1, 19990.00);
