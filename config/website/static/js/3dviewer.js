import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Scene creation
const container = document.getElementById('viewer-container');
const canvas = document.getElementById('3d-viewer');

const renderer = new THREE.WebGLRenderer({ canvas, alpha: true }); // alpha = true for transparent background.
renderer.setClearColor(0x000000, 0);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera( 75, container.clientWidth / container.clientHeight, 0.1, 1000 );
camera.position.set(0, 3, 7);
camera.lookAt(0, 0, 0);

const light = new THREE.AmbientLight(0xffffff, 5);
scene.add(light);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.25;
controls.screenSpacePanning = false;
controls.maxPolarAngle = Math.PI / 2;

resizeRendererToContainer(); // Set initial size

// Load the model.
let model;
const loader = new GLTFLoader();

loader.load(modelPath, function ( gltf ) {
    model = gltf.scene;
	scene.add(model);
}, undefined, function ( error ) {
	console.error( error );
} );

renderer.setAnimationLoop( animate );

// Resize function (updates renderer and camera)
function resizeRendererToContainer() {
    const width = container.clientWidth;
    const height = container.clientHeight;
    renderer.setSize(width, height); // Match canvas size to div
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
}

// Handle window resize event
window.addEventListener('resize', resizeRendererToContainer);

function animate() {
    if (model) { // Check if model is loaded before rotating
        model.rotation.y += 0.001;
    }
	renderer.render( scene, camera );
}