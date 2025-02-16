import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Light creation
const light_1 = new THREE.AmbientLight(0xffffff, 5);
const light_2 = new THREE.AmbientLight(0xffffff, 5);

// Scene creation
const container_1 = document.getElementById('viewer-container-1');
const container_2 = document.getElementById('viewer-container-2');
const canvas_1 = document.getElementById('3d-viewer-1');
const canvas_2 = document.getElementById('3d-viewer-2');
const renderer_1 = new THREE.WebGLRenderer({ canvas: canvas_1, alpha: true }); // alpha = true for transparent background.
const renderer_2 = new THREE.WebGLRenderer({ canvas: canvas_2, alpha: true }); // alpha = true for transparent background.
renderer_1.setClearColor(0x000000, 0);
renderer_2.setClearColor(0x000000, 0);
const scene_1 = new THREE.Scene();
const scene_2 = new THREE.Scene();

// Camera setup
const camera_1 = new THREE.PerspectiveCamera( 75, container_1.clientWidth / container_1.clientHeight, 0.1, 1000 );
const camera_2 = new THREE.PerspectiveCamera( 75, container_2.clientWidth / container_2.clientHeight, 0.1, 1000 );
camera_1.position.set(0, 3, 7);
camera_2.position.set(0, 3, 7);
camera_1.lookAt(0, 0, 0);
camera_2.lookAt(0, 0, 0);
scene_1.add(light_1);
scene_2.add(light_2);

const controls_1 = new OrbitControls(camera_1, renderer_1.domElement);
const controls_2= new OrbitControls(camera_2, renderer_2.domElement);
controls_1.enableDamping = true;
controls_1.dampingFactor = 0.25;
controls_1.screenSpacePanning = false;
controls_1.maxPolarAngle = Math.PI;
controls_2.enableDamping = true;
controls_2.dampingFactor = 0.25;
controls_2.screenSpacePanning = false;
controls_2.maxPolarAngle = Math.PI;

resizeRendererToContainer(container_1, renderer_1, camera_1); // Set initial size
resizeRendererToContainer(container_2, renderer_2, camera_2); // Set initial size

// Load the models.
let model_1, model_2;
const loader = new GLTFLoader();

loader.load(modelPath, function ( gltf ) {
    model_1 = gltf.scene;
	scene_1.add(model_1);
}, undefined, function ( error ) {
	console.error( error );
} );

loader.load(modelPath, function ( gltf ) {
    model_2 = gltf.scene;
	scene_2.add(model_2);
}, undefined, function ( error ) {
	console.error( error );
} );

renderer_1.setAnimationLoop( () => animate(model_1, renderer_1, scene_1, camera_1, controls_1) );
renderer_2.setAnimationLoop( () => animate(model_2, renderer_2, scene_2, camera_2, controls_2) );

// General functions

// Resize function (updates renderer and camera)
function resizeRendererToContainer(container, renderer, camera) {
    const width = container.clientWidth;
    const height = container.clientHeight;
    renderer.setSize(width, height); // Match canvas size to div
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
}

// Handle window resize event
window.addEventListener('resize', () => {
    resizeRendererToContainer(container_1, renderer_1, camera_1);
    resizeRendererToContainer(container_2, renderer_2, camera_2);
});

function animate(model, renderer, scene, camera, controls) {
    if (model) { // Check if model is loaded before rotating
        model.rotation.y += 0.001;
    }
    controls.update();
	renderer.render( scene, camera );
}