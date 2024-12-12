## Bronze

- [x] `config-flow` - Integration needs to be able to be set up via the UI
  - [ ] Uses `data-description` to give context to fields
  - [ ] Uses `ConfigEntry.data` and `ConfigEntry.options` correctly
- [x] `test-before-configure` - Test a connection in the config flow
- [x] `unique-config-entry` - Don't allow the same device or service to be able to be set up twice
- [x] `config-flow-test-coverage` - Full test coverage for the config flow
- [X] `runtime-data` - Use ConfigEntry.runtime_data to store runtime data
- [ ] `test-before-setup` - Check during integration initialization if we are able to set it up correctly
- [x] `appropriate-polling` - If it's a polling integration, set an appropriate polling interval
- [x] `entity-unique-id` - Entities have a unique ID
- [x] `has-entity-name` - Entities use has_entity_name = True
- [ ] `entity-event-setup` - Entities event setup
- [ ] `dependency-transparency` - Dependency transparency
- [x] `action-setup` - Service actions are registered in async_setup
- [x] `common-modules` - Place common patterns in common modules
- [ ] `docs-high-level-description` - The documentation includes a high-level description of the integration brand, product, or service
- [ ] `docs-installation-instructions` - The documentation provides step-by-step installation instructions for the integration, including, if needed, prerequisites
- [ ] `docs-removal-instructions` - The documentation provides removal instructions
- [ ] `docs-actions` - The documentation describes the provided service actions that can be used
- [x] `brands` - Has branding assets available for the integration

## Silver

- [ ] `config-entry-unloading` - Support config entry unloading
- [x] `log-when-unavailable` - If internet/device/service is unavailable, log once when unavailable and once when back connected
- [x] `entity-unavailable` - Mark entity unavailable if appropriate
- [x] `action-exceptions` - Service actions raise exceptions when encountering failures
- [x] `reauthentication-flow` - Reauthentication flow
- [ ] `parallel-updates` - Set Parallel updates
- [ ] `test-coverage` - Above 95% test coverage for all integration modules
- [x] `integration-owner` - Has an integration owner
- [ ] `docs-installation-parameters` - The documentation describes all integration installation parameters
- [ ] `docs-configuration-parameters` - The documentation describes all integration configuration options

## Gold

- [x] `entity-translations` - Entities have translated names
- [x] `entity-device-class` - Entities use device classes where possible
- [x] `devices` - The integration creates devices
- [x] `entity-category` - Entities are assigned an appropriate EntityCategory
- [x] `entity-disabled-by-default` - Integration disables less popular (or noisy) entities
- [ ] `discovery` - Can be discovered
- [ ] `stale-devices` - Clean up stale devices
- [ ] `diagnostics` - Implements diagnostics
- [ ] `exception-translations` - Exception messages are translatable
- [ ] `icon-translations` - Icon translations
- [x] `reconfiguration-flow` - Integrations should have a reconfigure flow
- [ ] `dynamic-devices` - Devices added after integration setup
- [ ] `discovery-update-info` - Integration uses discovery info to update network information
- [ ] `repair-issues` - Repair issues and repair flows are used when user intervention is needed
- [ ] `docs-use-cases` - The documentation describes use cases to illustrate how this integration can be used
- [ ] `docs-supported-devices` - The documentation describes known supported / unsupported devices
- [ ] `docs-supported-functions` - The documentation describes the supported functionality, including entities, and platforms
- [ ] `docs-data-update` - The documentation describes how data is updated
- [ ] `docs-known-limitations` - The documentation describes known limitations of the integration (not to be confused with bugs)
- [ ] `docs-troubleshooting` - The documentation provides troubleshooting information
- [ ] `docs-examples` - The documentation provides automation examples the user can use.

## Platinum

- [ ] `async-dependency` - Dependency is async
- [ ] `inject-websession` - The integration dependency supports passing in a websession
- [ ] `strict-typing` - Strict typing
