# CLI Coverage Matrix

**Last updated**: 2026-02-18
**RAPS CLI version**: Latest (26 top-level commands, ~173 total command paths)
**Test suite**: 263 tests across 25 files

## Coverage Summary

| Status | Count | Description |
|--------|-------|-------------|
| Tested | 100+ | Commands exercised by at least one SR test |
| Untested | ~70 | Mostly nested CRUD sub-subcommands (ACC modules, admin operations) |

Most untested commands are deep CRUD operations (e.g., `acc asset update`, `admin operation resume`) where the parent command is tested but not every sub-subcommand variant.

## Command Coverage

### auth (6 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `auth test` | Yes | SR-010 | test_01_auth.py | 2-legged auth test |
| `auth login` | Yes | SR-011 | test_01_auth.py | 3-legged OAuth |
| `auth logout` | Yes | SR-014 | test_01_auth.py | Destructive; token save/restore |
| `auth status` | Yes | SR-012 | test_01_auth.py | |
| `auth whoami` | Yes | SR-013 | test_01_auth.py | Also used in discovery.py |
| `auth inspect` | Yes | SR-015 | test_01_auth.py | |

### bucket (4 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `bucket create` | Yes | SR-050 | test_03_storage.py | |
| `bucket list` | Yes | SR-051 | test_03_storage.py | |
| `bucket info` | Yes | SR-052 | test_03_storage.py | |
| `bucket delete` | Yes | SR-063 | test_03_storage.py | In lifecycle |

### object (9 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `object upload` | Yes | SR-054 | test_03_storage.py | Single file |
| `object upload-batch` | Yes | SR-066 | test_03_storage.py | Parallel batch upload |
| `object download` | Yes | SR-058 | test_03_storage.py | |
| `object list` | Yes | SR-056 | test_03_storage.py | |
| `object delete` | Yes | SR-062 | test_03_storage.py | |
| `object signed-url` | Yes | SR-059 | test_03_storage.py | |
| `object info` | Yes | SR-057 | test_03_storage.py | |
| `object copy` | Yes | SR-060 | test_03_storage.py | |
| `object rename` | Yes | SR-061 | test_03_storage.py | |

### translate (6 subcommands + 5 preset sub-subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `translate start` | Yes | SR-090 | test_05_model_derivative.py | |
| `translate status` | Yes | SR-091 | test_05_model_derivative.py | |
| `translate manifest` | Yes | SR-092 | test_05_model_derivative.py | |
| `translate derivatives` | Yes | SR-093 | test_05_model_derivative.py | |
| `translate download` | Yes | SR-094 | test_05_model_derivative.py | |
| `translate preset list` | Yes | SR-095 | test_05_model_derivative.py | |
| `translate preset show` | Yes | SR-096 | test_05_model_derivative.py | |
| `translate preset create` | Yes | SR-097 | test_05_model_derivative.py | In lifecycle |
| `translate preset delete` | Yes | SR-098 | test_05_model_derivative.py | In lifecycle |
| `translate preset use` | Yes | SR-099 | test_05_model_derivative.py | |

### hub (2 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `hub list` | Yes | SR-070 | test_04_data_management.py | Also used in discovery.py |
| `hub info` | Yes | SR-071 | test_04_data_management.py | |

### project (2 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `project list` | Yes | SR-072 | test_04_data_management.py | Also used in discovery.py |
| `project info` | Yes | SR-073 | test_04_data_management.py | |

### folder (5 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `folder list` | Yes | SR-074 | test_04_data_management.py | |
| `folder create` | Yes | SR-075 | test_04_data_management.py | In lifecycle |
| `folder rename` | Yes | SR-076 | test_04_data_management.py | In lifecycle |
| `folder delete` | Yes | SR-077 | test_04_data_management.py | In lifecycle |
| `folder rights` | Yes | SR-078 | test_04_data_management.py | |

### item (5 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `item info` | Yes | SR-079 | test_04_data_management.py | |
| `item versions` | Yes | SR-080 | test_04_data_management.py | |
| `item create-from-oss` | Yes | SR-081 | test_04_data_management.py | In lifecycle |
| `item delete` | Yes | SR-082 | test_04_data_management.py | In lifecycle |
| `item rename` | Yes | SR-083 | test_04_data_management.py | In lifecycle |

### webhook (8 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `webhook list` | Yes | SR-180 | test_10_webhooks.py | |
| `webhook create` | Yes | SR-181 | test_10_webhooks.py | In lifecycle |
| `webhook get` | Yes | SR-182 | test_10_webhooks.py | |
| `webhook update` | Yes | SR-183 | test_10_webhooks.py | In lifecycle |
| `webhook delete` | Yes | SR-184 | test_10_webhooks.py | In lifecycle |
| `webhook events` | Yes | SR-185 | test_10_webhooks.py | |
| `webhook test` | Yes | SR-186 | test_10_webhooks.py | |
| `webhook verify-signature` | Yes | SR-187 | test_10_webhooks.py | |

### da (10 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `da engines` | Yes | SR-110 | test_06_design_automation.py | |
| `da appbundles` | Yes | SR-111 | test_06_design_automation.py | |
| `da appbundle-create` | Yes | SR-112 | test_06_design_automation.py | In lifecycle |
| `da appbundle-delete` | Yes | SR-113 | test_06_design_automation.py | In lifecycle |
| `da activities` | Yes | SR-114 | test_06_design_automation.py | |
| `da activity-create` | Yes | SR-115 | test_06_design_automation.py | In lifecycle |
| `da activity-delete` | Yes | SR-116 | test_06_design_automation.py | In lifecycle |
| `da run` | Yes | SR-117 | test_06_design_automation.py | |
| `da workitems` | Yes | SR-118 | test_06_design_automation.py | |
| `da status` | Yes | SR-119 | test_06_design_automation.py | |

### issue (8 subcommands + 3 comment sub-subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `issue list` | Yes | SR-130 | test_07_acc_issues.py | |
| `issue create` | Yes | SR-131 | test_07_acc_issues.py | In lifecycle |
| `issue update` | Yes | SR-132 | test_07_acc_issues.py | In lifecycle |
| `issue types` | Yes | SR-133 | test_07_acc_issues.py | |
| `issue comment list` | Yes | SR-134 | test_07_acc_issues.py | |
| `issue comment add` | Yes | SR-135 | test_07_acc_issues.py | In lifecycle |
| `issue comment delete` | Yes | SR-136 | test_07_acc_issues.py | In lifecycle |
| `issue attachments` | Yes | SR-137 | test_07_acc_issues.py | |
| `issue transition` | Yes | SR-138 | test_07_acc_issues.py | In lifecycle |
| `issue delete` | Yes | SR-139 | test_07_acc_issues.py | In lifecycle |

### acc (3 modules, 16 sub-subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `acc asset list` | Yes | SR-160 | test_09_acc_modules.py | |
| `acc asset get` | Yes | SR-161 | test_09_acc_modules.py | |
| `acc asset create` | Yes | SR-162 | test_09_acc_modules.py | In lifecycle |
| `acc asset update` | Yes | SR-163 | test_09_acc_modules.py | In lifecycle |
| `acc asset delete` | Yes | SR-164 | test_09_acc_modules.py | In lifecycle |
| `acc submittal list` | Yes | SR-165 | test_09_acc_modules.py | |
| `acc submittal get` | Yes | SR-166 | test_09_acc_modules.py | |
| `acc submittal create` | Yes | SR-167 | test_09_acc_modules.py | In lifecycle |
| `acc submittal update` | Yes | SR-168 | test_09_acc_modules.py | In lifecycle |
| `acc submittal delete` | Yes | SR-169 | test_09_acc_modules.py | In lifecycle |
| `acc checklist list` | Yes | SR-170 | test_09_acc_modules.py | |
| `acc checklist get` | Yes | SR-171 | test_09_acc_modules.py | |
| `acc checklist create` | Yes | SR-172 | test_09_acc_modules.py | In lifecycle |
| `acc checklist update` | Yes | SR-173 | test_09_acc_modules.py | In lifecycle |
| `acc checklist templates` | Yes | SR-174 | test_09_acc_modules.py | |

### rfi (5 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `rfi list` | Yes | SR-140 | test_08_acc_rfi.py | |
| `rfi get` | Yes | SR-141 | test_08_acc_rfi.py | |
| `rfi create` | Yes | SR-142 | test_08_acc_rfi.py | In lifecycle |
| `rfi update` | Yes | SR-143 | test_08_acc_rfi.py | In lifecycle |
| `rfi delete` | Yes | SR-144 | test_08_acc_rfi.py | In lifecycle |

### admin (user: 8, folder: 1, project: 4, operation: 4, company-list: 1)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `admin user list` | Yes | SR-190 | test_11_admin_users.py | |
| `admin user add` | Yes | SR-191 | test_11_admin_users.py | Bulk add |
| `admin user remove` | Yes | SR-192 | test_11_admin_users.py | Bulk remove |
| `admin user update` | Yes | SR-193 | test_11_admin_users.py | Bulk role update |
| `admin user add-to-project` | Yes | SR-194 | test_11_admin_users.py | Single project |
| `admin user remove-from-project` | Yes | SR-195 | test_11_admin_users.py | |
| `admin user update-in-project` | Yes | SR-196 | test_11_admin_users.py | |
| `admin user import` | Yes | SR-197 | test_11_admin_users.py | CSV import |
| `admin folder rights` | Yes | SR-230 | test_13_admin_folders.py | |
| `admin project list` | Yes | SR-210 | test_12_admin_projects.py | |
| `admin project create` | Yes | SR-211 | test_12_admin_projects.py | In lifecycle |
| `admin project update` | Yes | SR-212 | test_12_admin_projects.py | In lifecycle |
| `admin project archive` | Yes | SR-213 | test_12_admin_projects.py | In lifecycle |
| `admin operation status` | Yes | SR-200 | test_11_admin_users.py | |
| `admin operation list` | Yes | SR-201 | test_11_admin_users.py | |
| `admin operation resume` | No | — | — | Requires interrupted operation state |
| `admin operation cancel` | No | — | — | Requires in-progress operation |
| `admin company-list` | Yes | SR-202 | test_11_admin_users.py | |

### api (5 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `api get` | Yes | SR-280 | test_19_api_raw.py | |
| `api post` | Yes | SR-281 | test_19_api_raw.py | |
| `api put` | Yes | SR-282 | test_19_api_raw.py | |
| `api patch` | Yes | SR-283 | test_19_api_raw.py | |
| `api delete` | Yes | SR-284 | test_19_api_raw.py | |

### report (5 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `report rfi-summary` | Yes | SR-250 | test_15_reporting.py | |
| `report issues-summary` | Yes | SR-251 | test_15_reporting.py | |
| `report submittals-summary` | Yes | SR-252 | test_15_reporting.py | |
| `report checklists-summary` | Yes | SR-253 | test_15_reporting.py | |
| `report assets-summary` | Yes | SR-254 | test_15_reporting.py | |

### template (5 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `template list` | Yes | SR-240 | test_16_templates.py | |
| `template info` | Yes | SR-241 | test_16_templates.py | |
| `template create` | Yes | SR-242 | test_16_templates.py | In lifecycle |
| `template update` | Yes | SR-243 | test_16_templates.py | In lifecycle |
| `template archive` | Yes | SR-244 | test_16_templates.py | In lifecycle |

### reality (8 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `reality list` | Yes | SR-220 | test_14_reality_capture.py | |
| `reality create` | Yes | SR-221 | test_14_reality_capture.py | In lifecycle |
| `reality upload` | Yes | SR-222 | test_14_reality_capture.py | In lifecycle |
| `reality process` | Yes | SR-223 | test_14_reality_capture.py | In lifecycle |
| `reality status` | Yes | SR-224 | test_14_reality_capture.py | |
| `reality result` | Yes | SR-225 | test_14_reality_capture.py | |
| `reality formats` | Yes | SR-226 | test_14_reality_capture.py | |
| `reality delete` | Yes | SR-227 | test_14_reality_capture.py | In lifecycle |

### plugin (4 subcommands + 3 alias sub-subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `plugin list` | Yes | SR-260 | test_17_plugins.py | |
| `plugin enable` | Yes | SR-261 | test_17_plugins.py | In lifecycle |
| `plugin disable` | Yes | SR-262 | test_17_plugins.py | In lifecycle |
| `plugin alias list` | Yes | SR-263 | test_17_plugins.py | |
| `plugin alias add` | Yes | SR-264 | test_17_plugins.py | In lifecycle |
| `plugin alias remove` | Yes | SR-265 | test_17_plugins.py | In lifecycle |

### generate (1 subcommand)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `generate files` | Yes | SR-290 | test_20_generation.py | |

### demo (4 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `demo bucket-lifecycle` | Yes | SR-310 | test_22_demo.py | |
| `demo model-pipeline` | Yes | SR-311 | test_22_demo.py | |
| `demo data-management` | Yes | SR-312 | test_22_demo.py | |
| `demo batch-processing` | Yes | SR-313 | test_22_demo.py | |

### config (3 subcommands + 8 profile + 3 context sub-subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `config get` | Yes | SR-030 | test_02_config.py | |
| `config set` | Yes | SR-031 | test_02_config.py | |
| `config profile create` | Yes | SR-032 | test_02_config.py | In lifecycle |
| `config profile list` | Yes | SR-033 | test_02_config.py | |
| `config profile use` | Yes | SR-034 | test_02_config.py | |
| `config profile delete` | Yes | SR-035 | test_02_config.py | In lifecycle |
| `config profile current` | Yes | SR-036 | test_02_config.py | |
| `config profile export` | Yes | SR-037 | test_02_config.py | In lifecycle |
| `config profile import` | Yes | SR-038 | test_02_config.py | In lifecycle |
| `config profile diff` | Yes | SR-039 | test_02_config.py | |
| `config context show` | Yes | SR-040 | test_02_config.py | |
| `config context set` | Yes | SR-041 | test_02_config.py | |
| `config context clear` | Yes | SR-042 | test_02_config.py | |

### pipeline (3 subcommands)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `pipeline run` | Yes | SR-270 | test_18_pipelines.py | In lifecycle |
| `pipeline validate` | Yes | SR-271 | test_18_pipelines.py | |
| `pipeline sample` | Yes | SR-272 | test_18_pipelines.py | |

### completions (5 shell targets)

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `completions bash` | Yes | SR-302 | test_21_shell_serve.py | |
| `completions powershell` | Yes | SR-303 | test_21_shell_serve.py | |
| `completions zsh` | Yes | SR-304 | test_21_shell_serve.py | |
| `completions fish` | Yes | SR-305 | test_21_shell_serve.py | |
| `completions elvish` | Yes | SR-306 | test_21_shell_serve.py | |

### shell & serve

| Command | Tested | SR-ID(s) | Test File | Notes |
|---------|--------|----------|-----------|-------|
| `shell` | Yes | SR-300 | test_21_shell_serve.py | Interactive; timeout-based |
| `serve` | Yes | SR-301 | test_21_shell_serve.py | MCP server; timeout-based |

### Global options (tested via cross-cutting)

| Option | Tested | SR-ID(s) | Test File |
|--------|--------|----------|-----------|
| `--output json` | Yes | SR-540 | test_99_cross_cutting.py |
| `--output yaml` | Yes | SR-541 | test_99_cross_cutting.py |
| `--output csv` | Yes | SR-542 | test_99_cross_cutting.py |
| `--output table` | Yes | SR-543 | test_99_cross_cutting.py |
| `--output plain` | Yes | SR-544 | test_99_cross_cutting.py |
| `--help` | Yes | SR-530 | test_99_cross_cutting.py |
| `--version` | Yes | SR-531 | test_99_cross_cutting.py |

## Untested Commands

| Command | Rationale |
|---------|-----------|
| `admin operation resume` | Requires an interrupted bulk operation state (hard to reproduce in tests) |
| `admin operation cancel` | Requires an in-progress bulk operation (timing-dependent) |

All other commands are covered by at least one test.
