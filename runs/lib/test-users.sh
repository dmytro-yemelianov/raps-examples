#!/bin/bash
# test-users.sh — Real APS account users for sample run scripts
#
# Fill in real email addresses of users provisioned in your APS account.
# These are used by sections 11-admin-users, 12-admin-projects, 13-admin-folders,
# and 30-workflows.
#
# All emails can point to the SAME user if you only have one test account.
# The scripts use these for add/remove/update operations with --dry-run and -y.

# General-purpose test user (bulk add, remove, update operations)
: "${TEST_USER:=user@company.com}"

# Onboarding scenario user
: "${TEST_USER_NEW:=newuser@company.com}"

# Offboarding scenario user
: "${TEST_USER_DEPARTING:=departing@company.com}"

# Admin user for role-migration (downgrade admin -> viewer)
: "${TEST_USER_ADMIN:=admin1@co.com}"

# CSV batch import user
: "${TEST_USER_CSV:=user1@co.com}"

# Single add-to-project user
: "${TEST_USER_ADD:=new.user@company.com}"

# Project manager
: "${TEST_USER_PM:=pm@company.com}"

# Structural engineer
: "${TEST_USER_STRUCT:=struct@co.com}"

# MEP engineer
: "${TEST_USER_MEP:=mep@co.com}"

# Folder permissions target
: "${TEST_USER_FOLDER:=user@co.com}"

# Old admin for weekly maintenance downgrade
: "${TEST_USER_OLD_ADMIN:=admin@old.com}"

export TEST_USER TEST_USER_NEW TEST_USER_DEPARTING TEST_USER_ADMIN
export TEST_USER_CSV TEST_USER_ADD TEST_USER_PM TEST_USER_STRUCT
export TEST_USER_MEP TEST_USER_FOLDER TEST_USER_OLD_ADMIN
