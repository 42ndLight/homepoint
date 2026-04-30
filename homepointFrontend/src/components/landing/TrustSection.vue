<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    <div class="p-6 border-b border-gray-100">
      <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
        <i class="pi pi-users text-blue-600"></i>
        Role Definitions & Permissions
      </h2>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Role</th>
            <th class="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Description</th>
            <th class="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Permissions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="role in roles" :key="role.name">
            <td class="px-6 py-4 font-bold text-gray-900">{{ role.name }}</td>
            <td class="px-6 py-4 text-sm text-gray-600">{{ role.description }}</td>
            <td class="px-6 py-4">
              <div class="flex flex-wrap gap-1">
                <span v-for="perm in role.permissions" :key="perm" class="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                  {{ perm }}
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({
  roles: Array
})
</script>
