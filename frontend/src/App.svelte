<script lang="ts">
  import { onMount } from "svelte";

  const API_BASE = "http://localhost:8000/api";

  let originalImage: string | null = null;
  let originalImageFile: File | null = null;
  let clickedPoints: Array<{x: number, y: number, label: number}> = [];
  let originalImageDimensions: {width: number, height: number} | null = null;
  let isProcessing: boolean = false;
  let results: Array<{masked_image: string, mask: string, score: number}> = [];
  let isDarkMode: boolean = false;

  // Initialize dark mode from localStorage
  onMount(() => {
    const stored = localStorage.getItem("darkMode");
    isDarkMode = stored === "true";
    updateDarkMode();
  });

  function toggleDarkMode() {
    isDarkMode = !isDarkMode;
    localStorage.setItem("darkMode", String(isDarkMode));
    updateDarkMode();
  }

  function updateDarkMode() {
    if (isDarkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }

  function handleImageDrop(event: DragEvent) {
    event.preventDefault();
    const file = event.dataTransfer?.files[0];
    if (file && file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => {
        originalImage = e.target?.result as string;
        originalImageFile = file;
        clickedPoints = []; // Clear points when new image is loaded

        // Load image to get dimensions
        const img = new Image();
        img.onload = () => {
          originalImageDimensions = { width: img.naturalWidth, height: img.naturalHeight };
        };
        img.src = e.target?.result as string;
      };
      reader.readAsDataURL(file);
    }
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
  }

  function handleImageClick(event: MouseEvent) {
    if (!originalImageDimensions) return;

    // Get the actual img element, not the container
    const imgElement = (event.currentTarget as HTMLElement).querySelector('img');
    if (!imgElement) return;

    const rect = imgElement.getBoundingClientRect();

    // Get click position relative to the displayed image
    const displayX = event.clientX - rect.left;
    const displayY = event.clientY - rect.top;

    // Calculate scale factor between display size and actual image size
    const scaleX = originalImageDimensions.width / rect.width;
    const scaleY = originalImageDimensions.height / rect.height;

    // Convert to actual pixel coordinates (integers)
    const actualX = Math.round(displayX * scaleX);
    const actualY = Math.round(displayY * scaleY);

    // Add positive point (foreground) on left-click
    clickedPoints = [...clickedPoints, { x: actualX, y: actualY, label: 1 }];
  }

  function handleImageRightClick(event: MouseEvent) {
    event.preventDefault();
    if (!originalImageDimensions) return;

    // Get the actual img element, not the container
    const imgElement = (event.currentTarget as HTMLElement).querySelector('img');
    if (!imgElement) return;

    const rect = imgElement.getBoundingClientRect();

    // Get click position relative to the displayed image
    const displayX = event.clientX - rect.left;
    const displayY = event.clientY - rect.top;

    // Calculate scale factor between display size and actual image size
    const scaleX = originalImageDimensions.width / rect.width;
    const scaleY = originalImageDimensions.height / rect.height;

    // Convert to actual pixel coordinates (integers)
    const actualX = Math.round(displayX * scaleX);
    const actualY = Math.round(displayY * scaleY);

    // Add negative point (background) on right-click
    clickedPoints = [...clickedPoints, { x: actualX, y: actualY, label: 0 }];
  }

  function clearPoints() {
    clickedPoints = [];
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === "Escape") {
      clearPoints();
    }
  }

  async function uploadImage(file: File, imageType: string): Promise<string> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("image_type", imageType);

    const response = await fetch(`${API_BASE}/upload/image`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to upload ${imageType} image`);
    }

    const data = await response.json();
    return data.image_id;
  }

  async function handleRun() {
    if (!originalImage || !originalImageFile) {
      alert("Please upload an original image first");
      return;
    }

    if (clickedPoints.length === 0) {
      alert("Please select at least one point on the image");
      return;
    }

    isProcessing = true;
    results = [];

    try {
      // Upload image
      const originalImageId = await uploadImage(originalImageFile, "original");

      // Run mask generation synchronously
      const formData = new FormData();
      formData.append("original_image_id", originalImageId);

      // Separate points and labels for backend
      const points = clickedPoints.map(p => ({x: p.x, y: p.y}));
      const labels = clickedPoints.map(p => p.label);

      formData.append("points", JSON.stringify(points));
      formData.append("labels", JSON.stringify(labels));

      const response = await fetch(`${API_BASE}/run`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to generate masks");
      }

      const data = await response.json();
      results = data.results;
      isProcessing = false;
    } catch (error) {
      console.error("Error generating masks:", error);
      const errorMessage = error instanceof Error ? error.message : String(error);
      alert(`Error: ${errorMessage}`);
      isProcessing = false;
    }
  }
</script>

<svelte:window on:keydown={handleKeyDown} />

<div class="flex h-screen bg-gray-50 dark:bg-gray-900 relative">
  <!-- Dark Mode Toggle -->
  <button
    on:click={toggleDarkMode}
    class="absolute top-4 right-4 z-10 p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
    title={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
  >
    {#if isDarkMode}
      <svg class="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd" />
      </svg>
    {:else}
      <svg class="w-5 h-5 text-gray-700" fill="currentColor" viewBox="0 0 20 20">
        <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
      </svg>
    {/if}
  </button>

  <!-- Left Column (30%) -->
  <div class="w-[30%] border-r border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col">
    <!-- Original Image Upload -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex-1 flex flex-col min-h-0">
      <div class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex-shrink-0">
        Original Image
        {#if clickedPoints.length > 0}
          <span class="text-xs text-gray-500 dark:text-gray-400 ml-2">({clickedPoints.length} point{clickedPoints.length !== 1 ? 's' : ''})</span>
        {/if}
      </div>
      <div
        role="button"
        tabindex="0"
        on:drop={handleImageDrop}
        on:dragover={handleDragOver}
        class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4 hover:border-blue-500 transition-colors cursor-pointer bg-gray-50 dark:bg-gray-700 flex-1 flex items-center justify-center min-h-0"
      >
        {#if originalImage}
          <div class="relative h-full w-full flex items-center justify-center" on:click={handleImageClick} on:contextmenu={handleImageRightClick}>
            <img src={originalImage} alt="Original" class="max-w-full max-h-full object-contain" />
            {#if clickedPoints.length > 0 && originalImageDimensions}
              <svg
                class="absolute top-0 left-0 w-full h-full pointer-events-none"
                viewBox="0 0 {originalImageDimensions.width} {originalImageDimensions.height}"
                preserveAspectRatio="xMidYMid meet"
              >
                {#each clickedPoints as point}
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r="10"
                    fill={point.label === 1 ? "#3b82f6" : "#ef4444"}
                    stroke="white"
                    stroke-width="2"
                  />
                {/each}
              </svg>
            {/if}
          </div>
        {:else}
          <div class="text-center text-gray-500 dark:text-gray-400 py-8">
            <svg
              class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            <p class="mt-2">Drop image here</p>
          </div>
        {/if}
      </div>
      {#if originalImage}
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">Left-click: positive (blue) | Right-click: negative (red) | Esc: clear all</p>
      {/if}
    </div>

    <!-- Parameters -->
    <div class="p-4 flex-shrink-0">
      <button
        on:click={handleRun}
        disabled={!originalImage || isProcessing}
        class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors font-medium"
      >
        {isProcessing ? "Processing..." : "Run"}
      </button>
    </div>
  </div>

  <!-- Right Column (70%) -->
  <div class="w-[70%] flex flex-col bg-white dark:bg-gray-800">
    <!-- Header -->
    <div class="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 px-6 py-3">
      <h2 class="text-sm font-medium text-gray-700 dark:text-gray-300">
        Results
        {#if results.length > 0}
          <span class="text-xs text-gray-500 dark:text-gray-400 ml-2">({results.length} image{results.length !== 1 ? 's' : ''})</span>
        {/if}
      </h2>
    </div>

    <!-- Results Grid -->
    <div class="flex-1 p-6 overflow-hidden">
      {#if results.length > 0}
        <div class="h-full grid grid-rows-2 grid-cols-3 gap-4">
          <!-- Top row: Masked images -->
          {#each results as result, i}
            <div class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden flex items-center justify-center bg-gray-50 dark:bg-gray-700">
              <img src={result.masked_image} alt="Masked {i + 1}" class="max-w-full max-h-full object-contain" />
            </div>
          {/each}
          <!-- Bottom row: Grayscale masks -->
          {#each results as result, i}
            <div class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden flex items-center justify-center bg-gray-50 dark:bg-gray-700">
              <img src={result.mask} alt="Mask {i + 1}" class="max-w-full max-h-full object-contain" />
            </div>
          {/each}
        </div>
      {:else if isProcessing}
        <div class="flex items-center justify-center h-full">
          <div class="text-center">
            <div
              class="inline-block animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-600 mb-4"
            ></div>
            <p class="text-gray-600 dark:text-gray-400">Processing...</p>
          </div>
        </div>
      {:else}
        <div class="flex items-center justify-center h-full">
          <p class="text-gray-400 dark:text-gray-500 text-lg">
            No results yet. Upload an image and click "Run"
          </p>
        </div>
      {/if}
    </div>
  </div>
</div>
