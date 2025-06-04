import React, { useState } from "react";
import { View, Text, Image, TouchableOpacity } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import HomeScreen from "./Page/HomeScreen";
import LoginPage from "./Page/LoginPage";
import SignupPage from "./Page/SignupPage";
import Profile from "./Page/Profile";
import Shop from "./Page/Shop";
import Team from "./Page/Team";
import ForgotPage from "./Page/ForgotPage";
import { AntDesign } from "@expo/vector-icons";

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
 return (
  <Tab.Navigator
   screenOptions={{
    tabBarStyle: { backgroundColor: "black" },
   }}
  >
   <Tab.Screen
    name="Home"
    component={HomeScreen}
    options={{
     headerShown: false,
     tabBarLabel: ({ focused }) => <Text style={{ color: focused ? "orange" : "gray" }}>Home</Text>,
     tabBarIcon: ({ size, focused }) => (
      <AntDesign name="home" color={focused ? "orange" : "gray"} size={size} />
     ),
    }}
   />
   <Tab.Screen
    name="Shop"
    component={Shop}
    options={{
     headerShown: false,
     tabBarLabel: ({ focused }) => (
      <Text style={{ color: focused ? "orange" : "gray" }}>Shop</Text>
     ),
     tabBarIcon: ({ size, focused }) => (
      <AntDesign name="skin" color={focused ? "orange" : "gray"} size={size} />
     ),
    }}
   />
   <Tab.Screen
    name="Team"
    component={Team}
    options={{
     headerShown: false,
     tabBarLabel: ({ focused }) => <Text style={{ color: focused ? "orange" : "gray" }}>Team</Text>,
     tabBarIcon: ({ size, focused }) => (
      <AntDesign name="team" color={focused ? "orange" : "gray"} size={size} />
     ),
    }}
   />
   <Tab.Screen
    name="Profile"
    component={Profile}
    options={{
     headerShown: false,
     tabBarLabel: ({ focused }) => (
      <Text style={{ color: focused ? "orange" : "gray" }}>Profile</Text>
     ),
     tabBarIcon: ({ size, focused }) => (
      <AntDesign name="user" color={focused ? "orange" : "gray"} size={size} />
     ),
    }}
   />
  </Tab.Navigator>
 );
}

function App() {
 return (
  <NavigationContainer>
   <Stack.Navigator>
    <Stack.Screen name="SignUp" component={SignupPage} options={{ headerShown: false }} />
    <Stack.Screen name="Login" component={LoginPage} options={{ headerShown: false }} />
    <Stack.Screen name="Forgot" component={ForgotPage} options={{ headerShown: false }} />
    <Stack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
   </Stack.Navigator>
  </NavigationContainer>
 );
}

export default App;
