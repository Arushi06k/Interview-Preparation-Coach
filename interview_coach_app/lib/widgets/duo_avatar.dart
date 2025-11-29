import 'package:flutter/material.dart';

class DuoAvatar extends StatelessWidget {
  final double size;
  const DuoAvatar({this.size = 84, Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Placeholder circle; replace with mascot PNG in assets/images/mascot.png
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [Color(0xFF8359FF), Color(0xFFFF5EAB)]),
        borderRadius: BorderRadius.circular(20),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 10, offset: Offset(0,6))],
      ),
      child: Center(child: Text('ðŸ˜Š', style: TextStyle(fontSize: size/2))),
    );
  }
}
